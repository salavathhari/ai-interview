"""
AutomationService — Triggers on resume/JD/interview/coding changes.

Automatically regenerates skill gap analysis, updates weak topics,
and recalculates career readiness when underlying data changes.
Also records analytics events and refreshes analytics summaries.
"""

import json
import logging
from typing import Dict, Optional
from datetime import datetime, timezone
from sqlalchemy.orm import Session

logger = logging.getLogger(__name__)

from app.models.career import (
    ResumeAnalysis, JobDescription, SkillGapAnalysis, LearningRoadmap, CareerReadiness
)
from app.models.interview_session import InterviewSession
from app.models.coding_challenge import CodingSession
from app.models.intelligence import PerformanceMetrics, SkillAnalytics, CareerRecommendation
from app.models.generated_report import GeneratedReport
from app.services.skill_gap_engine import SkillGapEngine
from app.services.learning_progress_tracker import LearningProgressTracker


def _record_and_refresh(db: Session, user_id: int, event_type: str, category: str,
                        entity_type: str = None, entity_id: int = None, metrics: dict = None):
    """Record analytics event + refresh summary. Non-critical — swallow errors."""
    try:
        from app.routes.analytics import record_event, refresh_summary
        record_event(db, user_id, event_type, category, entity_type, entity_id, metrics)
        refresh_summary(db, user_id)
    except Exception:
        try:
            db.rollback()
        except Exception:
            pass


class AutomationService:
    """
    Automates skill gap recalculation and readiness updates
    whenever underlying data changes.
    """

    def __init__(self, db: Session):
        self.db = db

    def on_resume_change(self, user_id: int, resume_analysis_id: int):
        """
        When resume changes → regenerate skill gap analysis + recalculate ATS.
        """
        # Get latest JD if any
        latest_jd = self.db.query(JobDescription).filter(
            JobDescription.user_id == user_id
        ).order_by(JobDescription.created_at.desc()).first()

        # Run full analysis
        engine = SkillGapEngine(self.db)
        result = engine.analyze(
            user_id=user_id,
            resume_analysis_id=resume_analysis_id,
            job_description_id=latest_jd.id if latest_jd else None,
        )

        # Save new skill gap analysis
        analysis = engine.save_to_db(
            user_id, result,
            resume_analysis_id=resume_analysis_id,
            job_description_id=latest_jd.id if latest_jd else None,
        )
        engine.update_skill_analytics(user_id, result)
        engine.generate_career_recommendations(user_id, result)

        # Recalculate ATS score
        self._recalculate_ats(user_id, resume_analysis_id, latest_jd.id if latest_jd else None)

        # Update career readiness
        self._update_readiness(user_id, trigger_event="resume_upload")

        # Record analytics event
        _record_and_refresh(self.db, user_id, "resume_updated", "resume",
                           "resume_analysis", resume_analysis_id)

        # Mark reports as outdated
        self._mark_reports_outdated(user_id, "Resume data changed")

        return analysis

    def on_jd_change(self, user_id: int, job_description_id: int):
        """
        When JD changes → regenerate skill gap analysis, recalculate ATS, and update learning roadmap.
        """
        # Get latest resume analysis
        latest_resume = self.db.query(ResumeAnalysis).filter(
            ResumeAnalysis.user_id == user_id
        ).order_by(ResumeAnalysis.created_at.desc()).first()

        # Run full analysis
        engine = SkillGapEngine(self.db)
        result = engine.analyze(
            user_id=user_id,
            resume_analysis_id=latest_resume.id if latest_resume else None,
            job_description_id=job_description_id,
        )

        # Save new skill gap
        analysis = engine.save_to_db(
            user_id, result,
            resume_analysis_id=latest_resume.id if latest_resume else None,
            job_description_id=job_description_id,
        )
        engine.update_skill_analytics(user_id, result)
        engine.generate_career_recommendations(user_id, result)

        # Recalculate ATS score for latest resume
        if latest_resume:
            self._recalculate_ats(user_id, latest_resume.resume_id, job_description_id)

        # Update readiness
        self._update_readiness(user_id, trigger_event="jd_upload")

        # Update existing roadmap if any
        self._update_roadmap_from_new_gap(user_id, analysis.id)

        # Record analytics event
        _record_and_refresh(self.db, user_id, "jd_uploaded", "jd",
                           "job_description", job_description_id)

        # Mark reports as outdated
        self._mark_reports_outdated(user_id, "Job description changed")

        return analysis

    def on_interview_complete(self, user_id: int, interview_session_id: int):
        """
        When interview finishes → update weak topics and recalculate skill gap.
        """
        session = self.db.query(InterviewSession).filter(
            InterviewSession.id == interview_session_id
        ).first()

        if not session:
            return

        # Extract performance data
        topic_scores = {}
        for field, name in [
            ("score_dsa", "dsa"), ("score_dbms", "dbms"),
            ("score_os", "os"), ("score_cn", "computer_networks"),
            ("score_oop", "oop"), ("score_system_design", "system_design"),
            ("score_hr", "hr"), ("score_communication", "communication"),
        ]:
            val = getattr(session, field, None)
            if val is not None:
                topic_scores[name] = val

        weak = [t for t, s in topic_scores.items() if s < 60]
        strong = [t for t, s in topic_scores.items() if s >= 75]

        perf_data = {
            "overall_score": session.score,
            "topic_scores": topic_scores,
            "weak_topics": weak,
            "strong_topics": strong,
            "difficulty": session.difficulty,
            "role": session.role,
        }

        # Save performance metrics
        engine = SkillGapEngine(self.db)
        engine.save_performance_metrics(user_id, "interview", interview_session_id, perf_data)

        # Re-run analysis with updated data
        latest_jd = self.db.query(JobDescription).filter(
            JobDescription.user_id == user_id
        ).order_by(JobDescription.created_at.desc()).first()

        latest_resume = self.db.query(ResumeAnalysis).filter(
            ResumeAnalysis.user_id == user_id
        ).order_by(ResumeAnalysis.created_at.desc()).first()

        result = engine.analyze(
            user_id=user_id,
            resume_analysis_id=latest_resume.id if latest_resume else None,
            job_description_id=latest_jd.id if latest_jd else None,
        )

        engine.save_to_db(
            user_id, result,
            resume_analysis_id=latest_resume.id if latest_resume else None,
            job_description_id=latest_jd.id if latest_jd else None,
        )
        engine.update_skill_analytics(user_id, result)
        engine.generate_career_recommendations(user_id, result)

        # Update readiness
        self._update_readiness(user_id, trigger_event="interview")

        # Update adaptive interview questions
        self._update_interview_adaptation(user_id, weak)

        # Record analytics event
        _record_and_refresh(self.db, user_id, "interview_completed", "interview",
                           "interview_session", interview_session_id,
                           {"score": session.score, "role": session.role})

        # Mark reports as outdated
        self._mark_reports_outdated(user_id, "Interview completed")

    def on_coding_complete(self, user_id: int, coding_session_id: int):
        """
        When coding round finishes → update coding weaknesses.
        """
        session = self.db.query(CodingSession).filter(
            CodingSession.id == coding_session_id
        ).first()

        if not session:
            return

        # Extract coding performance
        topic_scores = {}
        if session.challenge and session.challenge.topics:
            for topic in session.challenge.topics:
                topic_scores[topic] = session.coding_score or 0

        weak = [t for t, s in topic_scores.items() if s < 60]
        strong = [t for t, s in topic_scores.items() if s >= 75]

        perf_data = {
            "overall_score": session.coding_score,
            "topic_scores": topic_scores,
            "weak_topics": weak,
            "strong_topics": strong,
        }

        # Save performance metrics
        engine = SkillGapEngine(self.db)
        engine.save_performance_metrics(user_id, "coding", coding_session_id, perf_data)

        # Re-run analysis
        latest_jd = self.db.query(JobDescription).filter(
            JobDescription.user_id == user_id
        ).order_by(JobDescription.created_at.desc()).first()

        latest_resume = self.db.query(ResumeAnalysis).filter(
            ResumeAnalysis.user_id == user_id
        ).order_by(ResumeAnalysis.created_at.desc()).first()

        result = engine.analyze(
            user_id=user_id,
            resume_analysis_id=latest_resume.id if latest_resume else None,
            job_description_id=latest_jd.id if latest_jd else None,
        )

        engine.save_to_db(
            user_id, result,
            resume_analysis_id=latest_resume.id if latest_resume else None,
            job_description_id=latest_jd.id if latest_jd else None,
        )
        engine.update_skill_analytics(user_id, result)
        engine.generate_career_recommendations(user_id, result)

        # Update readiness
        self._update_readiness(user_id, trigger_event="coding")

        # Update adaptive coding questions
        self._update_coding_adaptation(user_id, weak)

        # Record analytics event
        _record_and_refresh(self.db, user_id, "coding_completed", "coding",
                           "coding_session", coding_session_id,
                           {"score": session.coding_score})

        # Mark reports as outdated
        self._mark_reports_outdated(user_id, "Coding session completed")

    def on_learning_progress_change(self, user_id: int):
        """
        When any learning progress changes → update readiness + skill analytics.
        Called by LearningProgressTracker after topic completion.
        """
        self._update_readiness(user_id, trigger_event="learning")
        self._recalculate_skill_analytics(user_id)

        # Record analytics event
        _record_and_refresh(self.db, user_id, "learning_progress_updated", "learning")

        # Mark reports as outdated
        self._mark_reports_outdated(user_id, "Learning progress changed")

    def on_learning_topic_complete(self, user_id: int, roadmap_id: int, topic_name: str):
        """
        When learning topic completed → recalculate career readiness.
        """
        tracker = LearningProgressTracker(self.db)
        tracker.complete_topic(user_id, roadmap_id, topic_name)
        # readiness recalculation happens inside complete_topic

    def _recalculate_ats(self, user_id: int, resume_id: int, job_description_id: int = None):
        """Recalculate ATS score for a resume and update readiness."""
        from app.models.resume import Resume
        from app.services.career_service import CareerService
        from app.models.career import ResumeAnalysis

        resume = self.db.query(Resume).filter(
            Resume.id == resume_id,
            Resume.user_id == user_id,
        ).first()
        if not resume or not resume.extracted_text:
            return

        jd_text = None
        if job_description_id:
            jd = self.db.query(JobDescription).filter(
                JobDescription.id == job_description_id,
                JobDescription.user_id == user_id,
            ).first()
            if jd:
                jd_text = jd.raw_text

        analysis = CareerService.calculate_comprehensive_ats_score(resume.extracted_text, jd_text)

        # Update existing ResumeAnalysis with ATS score
        existing = self.db.query(ResumeAnalysis).filter(
            ResumeAnalysis.resume_id == resume_id,
            ResumeAnalysis.user_id == user_id,
        ).order_by(ResumeAnalysis.created_at.desc()).first()

        if existing:
            existing.ats_score = analysis["overall_score"]
            existing.ats_breakdown = json.dumps(analysis["breakdown"])
            existing.ats_suggestions = json.dumps([r["message"] for r in analysis.get("recommendations", [])])
            self.db.commit()

    def _update_readiness(self, user_id: int, trigger_event: str = "manual"):
        """Recalculate overall career readiness score with enhanced 10-component formula."""
        readiness = self.db.query(CareerReadiness).filter(
            CareerReadiness.user_id == user_id
        ).order_by(CareerReadiness.created_at.desc()).first()

        if not readiness:
            readiness = CareerReadiness(user_id=user_id)
            self.db.add(readiness)

        # Get latest interview score
        latest_interview = self.db.query(InterviewSession).filter(
            InterviewSession.user_id == user_id,
            InterviewSession.status == "completed",
        ).order_by(InterviewSession.ended_at.desc()).first()

        # Get latest coding score
        latest_coding = self.db.query(CodingSession).filter(
            CodingSession.user_id == user_id,
            CodingSession.status == "submitted",
        ).order_by(CodingSession.ended_at.desc()).first()

        # Get latest skill gap
        latest_gap = self.db.query(SkillGapAnalysis).filter(
            SkillGapAnalysis.user_id == user_id
        ).order_by(SkillGapAnalysis.created_at.desc()).first()

        # Get learning progress
        tracker = LearningProgressTracker(self.db)
        stats = tracker.get_stats(user_id)

        # Get project portfolio score (from resume projects + technologies)
        project_score = 0
        if readiness.resume_analysis_id:
            from app.models.career import ResumeAnalysis
            ra = self.db.query(ResumeAnalysis).filter(ResumeAnalysis.id == readiness.resume_analysis_id).first()
            if ra:
                project_count = 0
                tech_count = 0
                if ra.projects:
                    try:
                        projects = json.loads(ra.projects)
                        project_count = len(projects) if isinstance(projects, list) else 0
                    except (json.JSONDecodeError, TypeError):
                        pass
                if ra.technologies:
                    try:
                        techs = json.loads(ra.technologies)
                        tech_count = len(techs) if isinstance(techs, list) else 0
                    except (json.JSONDecodeError, TypeError):
                        pass
                # Score: 60% project count + 40% tech diversity
                project_score = min(100, project_count * 15 + tech_count * 3)

        # Update individual scores
        if latest_interview:
            readiness.interview_score = latest_interview.score
        if latest_coding:
            readiness.coding_score = latest_coding.coding_score
        if latest_gap:
            readiness.skill_gap_score = latest_gap.match_percentage

        # Calculate component scores
        resume_match = readiness.resume_match_score or 0
        ats = readiness.ats_score or 0
        skill_gap = readiness.skill_gap_score or 0
        interview = readiness.interview_score or 0
        coding = readiness.coding_score or 0

        # Learning score: based on completion rate and hours
        learning_score = min(100, stats["completion_rate"] * 1.0 + stats["total_hours_learned"] * 2)
        readiness.learning_score = round(learning_score, 1)

        # Project score already calculated above
        readiness.project_score = round(project_score, 1)

        # Consistency score: based on learning velocity and evidence count
        consistency = min(100, stats["learning_velocity_per_week"] * 20 + stats["completed"] * 5)
        readiness.consistency_score = round(consistency, 1)

        # Enhanced overall formula (10 components)
        overall = (
            resume_match * 0.20 +       # 20% - Resume quality
            ats * 0.10 +                 # 10% - ATS compatibility
            skill_gap * 0.20 +           # 20% - Skill alignment
            interview * 0.15 +           # 15% - Interview readiness
            coding * 0.10 +              # 10% - Coding skills
            learning_score * 0.10 +      # 10% - Learning progress
            project_score * 0.05 +       # 5%  - Project portfolio
            consistency * 0.05 +         # 5%  - Consistency
            (readiness.role_match_score or 0) * 0.03 +  # 3%  - Role match
            (readiness.company_match_score or 0) * 0.02  # 2%  - Company match
        )

        readiness.overall_score = round(min(100, max(0, overall)), 1)

        # Build detailed breakdown
        breakdown = {
            "resume_match": {"score": resume_match, "weight": 0.20, "weighted": round(resume_match * 0.20, 1)},
            "ats": {"score": ats, "weight": 0.10, "weighted": round(ats * 0.10, 1)},
            "skill_gap": {"score": skill_gap, "weight": 0.20, "weighted": round(skill_gap * 0.20, 1)},
            "interview": {"score": interview, "weight": 0.15, "weighted": round(interview * 0.15, 1)},
            "coding": {"score": coding, "weight": 0.10, "weighted": round(coding * 0.10, 1)},
            "learning": {"score": learning_score, "weight": 0.10, "weighted": round(learning_score * 0.10, 1)},
            "project": {"score": project_score, "weight": 0.05, "weighted": round(project_score * 0.05, 1)},
            "consistency": {"score": consistency, "weight": 0.05, "weighted": round(consistency * 0.05, 1)},
            "role_match": {"score": readiness.role_match_score or 0, "weight": 0.03, "weighted": round((readiness.role_match_score or 0) * 0.03, 1)},
            "company_match": {"score": readiness.company_match_score or 0, "weight": 0.02, "weighted": round((readiness.company_match_score or 0) * 0.02, 1)},
        }
        readiness.score_breakdown = json.dumps(breakdown)

        self.db.commit()

        # Save history snapshot
        try:
            from app.models.career import CareerReadinessHistory
            history = CareerReadinessHistory(
                user_id=user_id,
                overall_score=readiness.overall_score,
                resume_match_score=readiness.resume_match_score,
                ats_score=readiness.ats_score,
                interview_score=readiness.interview_score,
                coding_score=readiness.coding_score,
                skill_gap_score=readiness.skill_gap_score,
                learning_score=readiness.learning_score,
                trigger_event=trigger_event,
            )
            self.db.add(history)
            self.db.commit()
        except Exception:
            logger.debug("Failed to save career readiness history for user %s", user_id)
            self.db.rollback()  # Non-critical: don't fail readiness if history save fails

    def _recalculate_skill_analytics(self, user_id: int):
        """Recalculate skill analytics from all sources (resume, JD, learning, interview, coding)."""
        from app.models.resume import Resume

        # Get latest resume analysis
        latest_resume = self.db.query(ResumeAnalysis).filter(
            ResumeAnalysis.user_id == user_id
        ).order_by(ResumeAnalysis.created_at.desc()).first()

        if not latest_resume:
            return

        resume = self.db.query(Resume).filter(Resume.id == latest_resume.resume_id).first()
        if not resume or not resume.extracted_text:
            return

        # Re-extract skills from resume to refresh analytics
        from app.ml.models.skill_extractor import SkillExtractor
        extractor = SkillExtractor()
        skills = extractor.extract(resume.extracted_text)

        for skill_name, data in skills.items():
            existing = self.db.query(SkillAnalytics).filter(
                SkillAnalytics.user_id == user_id,
                SkillAnalytics.skill_name == skill_name,
            ).first()

            if existing:
                existing.proficiency_level = max(existing.proficiency_level, data.get("confidence", 50) * 100)
                existing.last_assessed = datetime.now(timezone.utc)
                existing.evidence_count += 1
            else:
                self.db.add(SkillAnalytics(
                    user_id=user_id,
                    skill_name=skill_name,
                    category="resume",
                    proficiency_level=data.get("confidence", 50) * 100,
                    source="resume",
                    evidence_count=1,
                    last_assessed=datetime.now(timezone.utc),
                ))

        self.db.commit()

    def _mark_reports_outdated(self, user_id: int, reason: str):
        """Mark all generated reports as outdated when underlying data changes."""
        try:
            self.db.query(GeneratedReport).filter(
                GeneratedReport.user_id == user_id,
                GeneratedReport.is_outdated == False,
            ).update({
                "is_outdated": True,
                "outdated_reason": reason,
            })
            self.db.commit()
        except Exception:
            logger.debug("Failed to mark reports outdated for user %s", user_id)
            self.db.rollback()  # Non-critical

    def _update_roadmap_from_new_gap(self, user_id: int, skill_gap_id: int):
        """Update existing roadmap or generate a new one when skill gap changes."""
        roadmap = self.db.query(LearningRoadmap).filter(
            LearningRoadmap.user_id == user_id,
            LearningRoadmap.status == "active",
        ).first()

        if roadmap:
            roadmap.skill_gap_id = skill_gap_id
            self.db.commit()
        else:
            # Auto-generate a roadmap when none exists
            try:
                from app.services.enhanced_roadmap_generator import EnhancedRoadmapGenerator
                skill_gap = self.db.query(SkillGapAnalysis).filter(
                    SkillGapAnalysis.id == skill_gap_id
                ).first()
                if skill_gap:
                    generator = EnhancedRoadmapGenerator(self.db)
                    roadmap_data = generator.generate_enhanced_roadmap(
                        user_id=user_id,
                        job_description=skill_gap.job_description or "",
                        resume_text="",
                        target_role=skill_gap.job_title or "Software Engineer",
                    )
                    from app.routes.career import save_roadmap_to_db
                    save_roadmap_to_db(self.db, user_id, roadmap_data, skill_gap_id=skill_gap_id)
            except Exception:
                logger.debug("Failed to auto-generate roadmap for user %s", user_id)

    def _update_interview_adaptation(self, user_id: int, weak_topics: list):
        """
        Mark weak topics for adaptive interview question generation.
        Interview engine should focus on weak areas.
        """
        # Store adaptation hints
        for topic in weak_topics:
            existing = self.db.query(SkillAnalytics).filter(
                SkillAnalytics.user_id == user_id,
                SkillAnalytics.skill_name == topic,
            ).first()

            if existing:
                existing.trend = "declining"
                existing.last_assessed = datetime.now(timezone.utc)
            else:
                self.db.add(SkillAnalytics(
                    user_id=user_id,
                    skill_name=topic,
                    category="interview",
                    proficiency_level=30,
                    source="interview",
                    trend="declining",
                    last_assessed=datetime.now(timezone.utc),
                ))

        self.db.commit()

    def _update_coding_adaptation(self, user_id: int, weak_topics: list):
        """
        Mark weak coding topics for adaptive question generation.
        Coding engine should focus on weak areas.
        """
        for topic in weak_topics:
            existing = self.db.query(SkillAnalytics).filter(
                SkillAnalytics.user_id == user_id,
                SkillAnalytics.skill_name == topic,
            ).first()

            if existing:
                existing.trend = "declining"
                existing.last_assessed = datetime.now(timezone.utc)
            else:
                self.db.add(SkillAnalytics(
                    user_id=user_id,
                    skill_name=topic,
                    category="coding",
                    proficiency_level=30,
                    source="coding",
                    trend="declining",
                    last_assessed=datetime.now(timezone.utc),
                ))

        self.db.commit()
