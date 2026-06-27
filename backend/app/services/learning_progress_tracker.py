"""
LearningProgressTracker — Per-topic tracking with readiness recalculation.

Tracks individual learning progress, auto-updates career readiness,
and generates recommendations based on progress.
"""

import json
from typing import Dict, List, Optional
from datetime import datetime, timezone
from sqlalchemy.orm import Session

from app.models.career import LearningRoadmap, SkillGapAnalysis, CareerReadiness
from app.models.intelligence import LearningProgress, SkillAnalytics


class LearningProgressTracker:
    """Tracks per-topic learning progress and recalculates readiness."""

    def __init__(self, db: Session):
        self.db = db

    def start_topic(self, user_id: int, roadmap_id: int, topic_name: str, skill_name: str = None,
                    estimated_hours: float = None, difficulty: str = None, priority: str = None) -> LearningProgress:
        """Mark a topic as in-progress."""
        try:
            existing = self.db.query(LearningProgress).filter(
                LearningProgress.user_id == user_id,
                LearningProgress.roadmap_id == roadmap_id,
                LearningProgress.topic_name == topic_name,
            ).first()

            if existing:
                existing.status = "in_progress"
                existing.started_at = existing.started_at or datetime.now(timezone.utc)
                self.db.commit()
                self.db.refresh(existing)
                return existing

            progress = LearningProgress(
                user_id=user_id,
                roadmap_id=roadmap_id,
                topic_name=topic_name,
                skill_name=skill_name,
                status="in_progress",
                estimated_hours=estimated_hours,
                difficulty=difficulty,
                priority=priority,
                started_at=datetime.now(timezone.utc),
            )
            self.db.add(progress)
            self.db.commit()
            self.db.refresh(progress)
            return progress
        except Exception:
            self.db.rollback()
            raise

    def complete_topic(self, user_id: int, roadmap_id: int, topic_name: str,
                       actual_hours: float = None, notes: str = None) -> LearningProgress:
        """Mark a topic as completed and update related data."""
        try:
            progress = self.db.query(LearningProgress).filter(
                LearningProgress.user_id == user_id,
                LearningProgress.roadmap_id == roadmap_id,
                LearningProgress.topic_name == topic_name,
            ).first()

            if not progress:
                raise ValueError(f"Topic '{topic_name}' not found in roadmap {roadmap_id}")

            progress.status = "completed"
            progress.progress_percentage = 100.0
            progress.completed_at = datetime.now(timezone.utc)
            if actual_hours is not None:
                progress.actual_hours = actual_hours
            if notes:
                progress.notes = notes

            self.db.commit()

            # Update roadmap progress
            self._update_roadmap_progress(roadmap_id)

            # Update skill analytics if skill_name is set
            if progress.skill_name:
                self._update_skill_analytics(user_id, progress.skill_name)

            # Recalculate career readiness
            self._recalculate_readiness(user_id)

            return progress
        except ValueError:
            raise
        except Exception:
            self.db.rollback()
            raise

    def master_topic(self, user_id: int, roadmap_id: int, topic_name: str) -> LearningProgress:
        """Mark a topic as mastered (beyond completed)."""
        try:
            progress = self.db.query(LearningProgress).filter(
                LearningProgress.user_id == user_id,
                LearningProgress.roadmap_id == roadmap_id,
                LearningProgress.topic_name == topic_name,
            ).first()

            if not progress:
                raise ValueError(f"Topic '{topic_name}' not found in roadmap {roadmap_id}")

            progress.status = "mastered"
            progress.progress_percentage = 100.0
            self.db.commit()

            # Mastery boosts skill analytics
            if progress.skill_name:
                self._boost_skill_mastery(user_id, progress.skill_name)

            self._recalculate_readiness(user_id)
            return progress
        except ValueError:
            raise
        except Exception:
            self.db.rollback()
            raise

    def update_progress(self, user_id: int, roadmap_id: int, topic_name: str,
                        percentage: float, actual_hours: float = None) -> LearningProgress:
        """Update partial progress on a topic."""
        try:
            progress = self.db.query(LearningProgress).filter(
                LearningProgress.user_id == user_id,
                LearningProgress.roadmap_id == roadmap_id,
                LearningProgress.topic_name == topic_name,
            ).first()

            if not progress:
                raise ValueError(f"Topic '{topic_name}' not found in roadmap {roadmap_id}")

            progress.progress_percentage = min(100.0, max(0.0, percentage))
            if progress.status == "not_started":
                progress.status = "in_progress"
                progress.started_at = datetime.now(timezone.utc)
            if actual_hours is not None:
                progress.actual_hours = actual_hours

            self.db.commit()
            return progress
        except ValueError:
            raise
        except Exception:
            self.db.rollback()
            raise

    def get_progress(self, user_id: int, roadmap_id: int = None) -> List[Dict]:
        """Get all learning progress for a user, optionally filtered by roadmap."""
        try:
            query = self.db.query(LearningProgress).filter(LearningProgress.user_id == user_id)
            if roadmap_id:
                query = query.filter(LearningProgress.roadmap_id == roadmap_id)

            progress_list = query.order_by(LearningProgress.created_at.desc()).all()

            return [
                {
                    "id": p.id,
                    "roadmap_id": p.roadmap_id,
                    "topic_name": p.topic_name,
                    "skill_name": p.skill_name,
                    "status": p.status,
                    "progress_percentage": p.progress_percentage,
                    "estimated_hours": p.estimated_hours,
                    "actual_hours": p.actual_hours,
                    "difficulty": p.difficulty,
                    "priority": p.priority,
                    "started_at": p.started_at.isoformat() if p.started_at else None,
                    "completed_at": p.completed_at.isoformat() if p.completed_at else None,
                    "notes": p.notes,
                }
                for p in progress_list
            ]
        except Exception:
            return []

    def get_stats(self, user_id: int) -> Dict:
        """Get learning statistics for a user."""
        try:
            all_progress = self.db.query(LearningProgress).filter(
                LearningProgress.user_id == user_id
            ).all()

            completed = [p for p in all_progress if p.status in ("completed", "mastered")]
            in_progress = [p for p in all_progress if p.status == "in_progress"]
            total_hours = sum(p.actual_hours or 0 for p in all_progress)
            estimated_hours = sum(p.estimated_hours or 0 for p in all_progress)

            # Learning velocity: completed topics per week
            if completed:
                dates = [p.completed_at for p in completed if p.completed_at]
                if dates:
                    earliest = min(dates)
                    weeks = max(1, (datetime.now(timezone.utc) - earliest).days / 7)
                    velocity = round(len(completed) / weeks, 1)
                else:
                    velocity = 0
            else:
                velocity = 0

            mastered = [p for p in all_progress if p.status == "mastered"]

            return {
                "total_topics": len(all_progress),
                "completed": len(completed),
                "in_progress": len(in_progress),
                "not_started": len(all_progress) - len(completed) - len(in_progress),
                "mastered": len(mastered),
                "total_hours_learned": round(total_hours, 1),
                "estimated_hours": round(estimated_hours, 1),
                "learning_velocity_per_week": velocity,
                "completion_rate": round(len(completed) / max(1, len(all_progress)) * 100, 1),
            }
        except Exception:
            return {
                "total_topics": 0, "completed": 0, "in_progress": 0,
                "not_started": 0, "mastered": 0, "total_hours_learned": 0,
                "estimated_hours": 0, "learning_velocity_per_week": 0,
                "completion_rate": 0,
            }

    def _update_roadmap_progress(self, roadmap_id: int):
        """Update the parent roadmap's progress percentage and advance current phase."""
        try:
            roadmap = self.db.query(LearningRoadmap).filter(LearningRoadmap.id == roadmap_id).first()
            if not roadmap:
                return

            all_progress = self.db.query(LearningProgress).filter(
                LearningProgress.roadmap_id == roadmap_id
            ).all()

            if not all_progress:
                return

            completed_count = sum(1 for p in all_progress if p.status in ("completed", "mastered"))
            total = len(all_progress)
            percentage = round((completed_count / total) * 100, 1) if total > 0 else 0

            roadmap.progress_percentage = percentage

            # Update completed_topics list
            completed_names = [p.topic_name for p in all_progress if p.status in ("completed", "mastered")]
            roadmap.completed_topics = json.dumps(completed_names)

            # Advance current_phase_index if all topics in current phase are completed
            try:
                phases = json.loads(roadmap.phases) if roadmap.phases else []
                current_idx = roadmap.current_phase_index or 0

                if phases and current_idx < len(phases):
                    current_phase = phases[current_idx]
                    phase_topics_raw = current_phase.get("topics", [])
                    # Topics can be strings or dicts with a "topic" key
                    phase_topic_names = []
                    for t in phase_topics_raw:
                        if isinstance(t, str):
                            phase_topic_names.append(t)
                        elif isinstance(t, dict):
                            phase_topic_names.append(t.get("topic", t.get("name", "")))
                    if phase_topic_names:
                        phase_completed = all(t in completed_names for t in phase_topic_names)
                        if phase_completed and current_idx < len(phases) - 1:
                            roadmap.current_phase_index = current_idx + 1
            except (json.JSONDecodeError, KeyError, TypeError, AttributeError):
                pass

            # Auto-complete roadmap
            if percentage >= 100 and roadmap.status == "active":
                roadmap.status = "completed"

            self.db.commit()
        except Exception:
            self.db.rollback()

    def _update_skill_analytics(self, user_id: int, skill_name: str):
        """Update skill analytics when a learning topic is completed."""
        try:
            existing = self.db.query(SkillAnalytics).filter(
                SkillAnalytics.user_id == user_id,
                SkillAnalytics.skill_name == skill_name,
            ).first()

            if existing:
                existing.proficiency_level = min(100, existing.proficiency_level + 20)
                existing.trend = "improving"
                existing.last_assessed = datetime.now(timezone.utc)
                existing.evidence_count += 1
            else:
                self.db.add(SkillAnalytics(
                    user_id=user_id,
                    skill_name=skill_name,
                    category="learning",
                    proficiency_level=40,
                    source="learning",
                    trend="improving",
                    evidence_count=1,
                    last_assessed=datetime.now(timezone.utc),
                ))

            self.db.commit()
        except Exception:
            self.db.rollback()

    def _boost_skill_mastery(self, user_id: int, skill_name: str):
        """Boost skill analytics when a topic is mastered."""
        try:
            existing = self.db.query(SkillAnalytics).filter(
                SkillAnalytics.user_id == user_id,
                SkillAnalytics.skill_name == skill_name,
            ).first()

            if existing:
                existing.proficiency_level = min(100, existing.proficiency_level + 30)
                existing.trend = "improving"
                existing.last_assessed = datetime.now(timezone.utc)
            else:
                self.db.add(SkillAnalytics(
                    user_id=user_id,
                    skill_name=skill_name,
                    category="learning",
                    proficiency_level=70,
                    source="learning",
                    trend="improving",
                    evidence_count=1,
                    last_assessed=datetime.now(timezone.utc),
                ))

            self.db.commit()
        except Exception:
            self.db.rollback()

    def _recalculate_readiness(self, user_id: int):
        """Recalculate career readiness after learning progress update."""
        try:
            readiness = self.db.query(CareerReadiness).filter(
                CareerReadiness.user_id == user_id
            ).order_by(CareerReadiness.created_at.desc()).first()

            if not readiness:
                return

            resume_match = readiness.resume_match_score or 0
            ats = readiness.ats_score or 0
            skill_gap = readiness.skill_gap_score or 0
            interview = readiness.interview_score or 0
            coding = readiness.coding_score or 0

            stats = self.get_stats(user_id)
            learning_bonus = min(15, stats["completion_rate"] * 0.15)

            overall = (
                resume_match * 0.25 +
                ats * 0.15 +
                skill_gap * 0.25 +
                interview * 0.20 +
                coding * 0.15 +
                learning_bonus
            )

            readiness.overall_score = round(min(100, overall), 1)
            self.db.commit()
        except Exception:
            self.db.rollback()
