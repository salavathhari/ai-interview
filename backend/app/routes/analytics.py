"""
Analytics Engine — Complete BI layer.

Endpoints:
  GET /analytics/dashboard     — Full dashboard (all sections)
  GET /analytics/interview     — Interview-specific analytics
  GET /analytics/coding        — Coding-specific analytics
  GET /analytics/skills        — Skill heatmap & analytics
  GET /analytics/learning      — Learning progress analytics
  GET /analytics/career        — Career readiness analytics
  GET /analytics/topics        — Topic-wise performance
  GET /analytics/history       — Historical trends
  GET /analytics/predictions   — Predictive analytics + recommendations
"""

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from sqlalchemy import func, desc, and_, case
from datetime import datetime, timedelta, timezone
from typing import Optional
import traceback
import json

from app.database import get_db
from app.auth.utils import get_current_user
from app.models.user import User
from app.models.interview_session import InterviewSession
from app.models.question import Question
from app.models.interview_question_metric import InterviewQuestionMetric
from app.models.coding_challenge import CodingChallenge, CodingSubmission, CodingSession
from app.models.career import (
    ResumeAnalysis, SkillGapAnalysis, LearningRoadmap,
    CareerReadiness, CareerReadinessHistory, JobDescription,
)
from app.models.intelligence import (
    SkillAnalytics, LearningProgress, PerformanceMetrics, CareerRecommendation,
)
from app.models.analytics import AnalyticsEvent, AnalyticsSummary
from app.schemas.analytics import (
    AnalyticsResponse, TopicMetric, TrendPoint,
    CodingAnalyticsResponse, SkillAnalyticsResponse, SkillHeatmapItem,
    LearningAnalyticsResponse, CareerAnalyticsResponse,
    TopicAnalyticsResponse, HistoricalTrendResponse,
    PredictionResponse, RecommendationResponse,
)

router = APIRouter(prefix="/analytics", tags=["analytics"])

# ─── Normalization ──────────────────────────────────────────────────────────

TOPIC_NORM = {
    "computer networks": "Computer Networks", "networking": "Computer Networks", "cn": "Computer Networks",
    "dbms": "DBMS", "sql": "DBMS", "database": "DBMS",
    "data structures & algorithms": "DSA", "dsa": "DSA",
    "operating systems": "OS", "os": "OS",
    "object oriented programming": "OOP", "oop": "OOP",
    "system design": "System Design",
    "projects": "Projects", "project discussion": "Projects", "project": "Projects",
    "hr": "HR", "behavioral": "HR", "hr round": "HR",
    "react": "Frontend", "javascript": "Frontend", "js": "Frontend",
    "html/css": "Frontend", "html": "Frontend", "css": "Frontend",
    "python": "Programming", "machine learning": "ML", "ml": "ML",
    "role-specific skills": "Role-Specific",
}

CODING_TOPICS = [
    "Arrays", "Strings", "HashMap", "Stack", "Linked List",
    "Tree", "Graph", "Dynamic Programming", "Greedy",
    "Backtracking", "Binary Search", "Design", "Sorting",
]

SKILL_CATEGORIES = {
    "python": "programming", "java": "programming", "c++": "programming",
    "javascript": "programming", "typescript": "programming", "go": "programming",
    "rust": "programming", "c": "programming", "c#": "programming",
    "react": "framework", "angular": "framework", "vue": "framework",
    "node.js": "framework", "express": "framework", "django": "framework",
    "fastapi": "framework", "flask": "framework", "spring": "framework",
    "postgresql": "database", "mysql": "database", "mongodb": "database",
    "redis": "database", "sqlite": "database", "sql": "database",
    "aws": "cloud", "gcp": "cloud", "azure": "cloud",
    "docker": "devops", "kubernetes": "devops", "ci/cd": "devops",
    "git": "tool", "linux": "tool", "figma": "tool",
    "sql": "database", "rest api": "architecture", "graphql": "architecture",
}


def _norm_topic(raw: str) -> str:
    t = raw.strip().lower()
    return TOPIC_NORM.get(t, raw.strip())


def _skill_category(skill: str) -> str:
    return SKILL_CATEGORIES.get(skill.lower().strip(), "other")


def _parse_json_field(val) -> list | dict:
    if not val:
        return []
    try:
        return json.loads(val)
    except (json.JSONDecodeError, TypeError):
        return []


# ─── Event Collection ──────────────────────────────────────────────────────

def record_event(db: Session, user_id: int, event_type: str, event_category: str,
                 entity_type: str = None, entity_id: int = None,
                 metrics: dict = None, metadata: dict = None):
    """Record an analytics event."""
    event = AnalyticsEvent(
        user_id=user_id,
        event_type=event_type,
        event_category=event_category,
        entity_type=entity_type,
        entity_id=entity_id,
        metrics_json=json.dumps(metrics) if metrics else None,
        metadata_json=json.dumps(metadata) if metadata else None,
    )
    db.add(event)
    db.commit()
    return event


def refresh_summary(db: Session, user_id: int):
    """Rebuild analytics_summary from all data sources."""
    summary = db.query(AnalyticsSummary).filter(AnalyticsSummary.user_id == user_id).first()
    if not summary:
        summary = AnalyticsSummary(user_id=user_id)
        db.add(summary)

    # Interview stats
    completed = db.query(InterviewSession).filter(
        InterviewSession.user_id == user_id,
        InterviewSession.status == "completed",
    ).all()
    summary.total_interviews = len(completed)
    scores = [s.score for s in completed if s.score is not None]
    summary.completed_interviews = len(scores)
    summary.avg_interview_score = round(sum(scores) / len(scores), 1) if scores else 0.0
    if completed:
        summary.last_interview_at = max(s.ended_at or s.started_at for s in completed)

    # Coding stats
    coding_sessions = db.query(CodingSession).filter(CodingSession.user_id == user_id).all()
    summary.total_coding_sessions = len(coding_sessions)
    submissions = db.query(CodingSubmission).filter(CodingSubmission.user_id == user_id).all()
    summary.total_submissions = len(submissions)
    correctness = [s.correctness_score for s in submissions if s.correctness_score is not None]
    summary.avg_correctness = round(sum(correctness) / len(correctness), 1) if correctness else 0.0
    coding_scores = [s.coding_score for s in coding_sessions if s.coding_score is not None]
    summary.avg_coding_score = round(sum(coding_scores) / len(coding_scores), 1) if coding_scores else 0.0
    if coding_sessions:
        summary.last_coding_at = max(s.ended_at or s.started_at for s in coding_sessions)

    # Learning stats
    progress_items = db.query(LearningProgress).filter(LearningProgress.user_id == user_id).all()
    summary.completed_topics = len([p for p in progress_items if p.status in ("completed", "mastered")])
    summary.total_topics = len(progress_items)
    hours = [p.actual_hours for p in progress_items if p.actual_hours is not None]
    summary.total_learning_hours = round(sum(hours), 1) if hours else 0.0
    if progress_items:
        dates_with_activity = [p.completed_at or p.created_at for p in progress_items if p.completed_at or p.created_at]
        recent = max(dates_with_activity, default=None) if dates_with_activity else None
        summary.last_learning_at = recent

    # Skill stats
    skills = db.query(SkillAnalytics).filter(SkillAnalytics.user_id == user_id).all()
    summary.skills_learned = len([s for s in skills if s.proficiency_level >= 40])
    summary.skills_mastered = len([s for s in skills if s.proficiency_level >= 80])

    # Career readiness
    readiness = db.query(CareerReadiness).filter(
        CareerReadiness.user_id == user_id
    ).order_by(CareerReadiness.created_at.desc()).first()
    if readiness:
        summary.career_readiness_score = readiness.overall_score or 0.0
        summary.ats_score = readiness.ats_score or 0.0
        summary.resume_match_score = readiness.resume_match_score or 0.0
        summary.skill_gap_score = readiness.skill_gap_score or 0.0

    # Learning streak
    from datetime import date
    learning_dates = set()
    for p in progress_items:
        if p.completed_at:
            learning_dates.add(p.completed_at.date())
    streak = 0
    d = date.today()
    while d in learning_dates:
        streak += 1
        d -= timedelta(days=1)
    summary.learning_streak_days = streak

    summary.updated_at = datetime.now(timezone.utc)
    db.commit()
    return summary


# ─── Interview Analytics ───────────────────────────────────────────────────

def _get_interview_analytics(db: Session, user_id: int) -> dict:
    """Build interview analytics from InterviewSession + Question + Metric tables."""
    avg_score = db.query(func.avg(InterviewSession.score)).filter(
        InterviewSession.user_id == user_id,
        InterviewSession.status == "completed",
    ).scalar() or 0.0

    total = db.query(func.count(InterviewSession.id)).filter(
        InterviewSession.user_id == user_id,
        InterviewSession.status == "completed",
    ).scalar() or 0

    # Topic metrics
    raw = db.query(Question.topic, Question.score).join(InterviewSession).filter(
        InterviewSession.user_id == user_id,
        Question.score.isnot(None),
        Question.topic.isnot(None),
    ).all()

    topic_groups = {}
    for topic, score in raw:
        norm = _norm_topic(topic)
        topic_groups.setdefault(norm, []).append(score)

    all_topics = [
        TopicMetric(topic=t, average_score=round(sum(s) / len(s), 1), question_count=len(s))
        for t, s in topic_groups.items()
    ]
    weak = sorted(all_topics, key=lambda x: x.average_score)[:3]
    strong = sorted(all_topics, key=lambda x: x.average_score, reverse=True)[:3]

    # Trends
    trends = db.query(
        InterviewSession.started_at, InterviewSession.score,
    ).filter(
        InterviewSession.user_id == user_id,
        InterviewSession.status == "completed",
        InterviewSession.score.isnot(None),
    ).order_by(InterviewSession.started_at.desc()).limit(10).all()

    progress = [TrendPoint(date=t.started_at, score=round(float(t.score), 1)) for t in reversed(trends)]

    # Role distribution
    roles = db.query(InterviewSession.role, func.count(InterviewSession.id)).filter(
        InterviewSession.user_id == user_id,
    ).group_by(InterviewSession.role).all()
    role_dist = {r: c for r, c in roles}

    # Metric averages
    metric_avgs = db.query(
        func.avg(Question.score_accuracy),
        func.avg(Question.score_communication),
        func.avg(Question.score_confidence),
        func.avg(Question.score_completeness),
    ).join(InterviewSession).filter(
        InterviewSession.user_id == user_id,
        Question.score.isnot(None),
    ).first()

    # Timing
    timing = db.query(
        InterviewQuestionMetric.time_taken,
        InterviewQuestionMetric.time_limit,
        InterviewQuestionMetric.was_auto_submitted,
        InterviewQuestionMetric.warning_triggered,
    ).join(InterviewSession).filter(
        InterviewSession.user_id == user_id,
        InterviewQuestionMetric.time_taken.isnot(None),
        InterviewQuestionMetric.time_limit.isnot(None),
        InterviewQuestionMetric.time_limit > 0,
    ).all()

    avg_speed = 0.0
    hesitation = 0.0
    pressure = 100.0
    conf = float(metric_avgs[2] or 0.0)

    if timing:
        ratios = [min(r.time_taken / r.time_limit, 1.0) for r in timing]
        avg_speed = sum(r.time_taken for r in timing) / len(timing)
        hesitation = (sum(ratios) / len(ratios)) * 100
        pressure_events = [r for r in timing if r.warning_triggered or r.was_auto_submitted]
        if pressure_events:
            successful = [r for r in pressure_events if not r.was_auto_submitted]
            pressure = (len(successful) / len(pressure_events)) * 100
        conf = max(0.0, min(10.0, conf - (hesitation / 100)))

    # Improvement rate
    all_scores = db.query(InterviewSession.score).filter(
        InterviewSession.user_id == user_id,
        InterviewSession.status == "completed",
        InterviewSession.score.isnot(None),
    ).order_by(InterviewSession.started_at.asc()).all()

    improvement = 0.0
    if len(all_scores) >= 2:
        early = sum(s.score for s in all_scores[:2]) / 2
        recent = sum(s.score for s in all_scores[-2:]) / 2
        if early > 0:
            improvement = ((recent - early) / early) * 100

    return {
        "average_score": round(float(avg_score), 1),
        "total_interviews": total,
        "weak_topics": weak,
        "strong_topics": strong,
        "progress_trends": progress,
        "role_distribution": role_dist,
        "avg_accuracy": round(float(metric_avgs[0] or 0.0), 1),
        "avg_communication": round(float(metric_avgs[1] or 0.0), 1),
        "avg_confidence": round(float(metric_avgs[2] or 0.0), 1),
        "avg_completeness": round(float(metric_avgs[3] or 0.0), 1),
        "average_response_speed": round(avg_speed, 1),
        "hesitation_score": round(hesitation, 1),
        "pressure_handling": round(pressure, 1),
        "confidence_estimation": round(conf, 1),
        "improvement_rate": round(improvement, 1),
    }


# ─── Coding Analytics ─────────────────────────────────────────────────────

def _get_coding_analytics(db: Session, user_id: int) -> CodingAnalyticsResponse:
    sessions = db.query(CodingSession).filter(CodingSession.user_id == user_id).all()
    submissions = db.query(CodingSubmission).filter(CodingSubmission.user_id == user_id).all()

    total_sessions = len(sessions)
    total_submissions = len(submissions)

    correctness = [s.correctness_score for s in submissions if s.correctness_score is not None]
    avg_correctness = round(sum(correctness) / len(correctness), 1) if correctness else 0.0

    runtimes = [s.runtime_ms for s in submissions if s.runtime_ms is not None]
    avg_runtime = round(sum(runtimes) / len(runtimes), 1) if runtimes else 0.0

    memories = [s.memory_kb for s in submissions if s.memory_kb is not None]
    avg_memory = round(sum(memories) / len(memories), 1) if memories else 0.0

    ai_scores = [s.ai_score for s in submissions if s.ai_score is not None]
    avg_ai = round(sum(ai_scores) / len(ai_scores), 1) if ai_scores else 0.0

    # Language distribution
    lang_dist = {}
    for s in submissions:
        lang_dist[s.language] = lang_dist.get(s.language, 0) + 1

    # Difficulty distribution
    diff_dist = {}
    for sess in sessions:
        if sess.challenge:
            d = sess.challenge.difficulty
            diff_dist[d] = diff_dist.get(d, 0) + 1

    # Topic performance
    topic_scores = {}
    for sess in sessions:
        if sess.challenge and sess.challenge.topics:
            for topic in sess.challenge.topics:
                topic_scores.setdefault(topic, []).append(sess.coding_score or 0)
    topic_perf = [
        TopicMetric(topic=t, average_score=round(sum(s) / len(s), 1), question_count=len(s))
        for t, s in topic_scores.items()
    ]

    # Recent trends
    recent = db.query(CodingSession).filter(
        CodingSession.user_id == user_id,
        CodingSession.status == "submitted",
        CodingSession.coding_score.isnot(None),
    ).order_by(CodingSession.ended_at.desc()).limit(10).all()

    trends = [
        TrendPoint(date=s.ended_at or s.started_at, score=round(float(s.coding_score), 1))
        for s in reversed(recent)
    ]

    # Improvement
    all_cs = db.query(CodingSession.coding_score).filter(
        CodingSession.user_id == user_id,
        CodingSession.status == "submitted",
        CodingSession.coding_score.isnot(None),
    ).order_by(CodingSession.started_at.asc()).all()

    improvement = 0.0
    if len(all_cs) >= 2:
        early = sum(s.coding_score for s in all_cs[:2]) / 2
        recent_avg = sum(s.coding_score for s in all_cs[-2:]) / 2
        if early > 0:
            improvement = ((recent_avg - early) / early) * 100

    return CodingAnalyticsResponse(
        total_sessions=total_sessions,
        total_submissions=total_submissions,
        avg_correctness=avg_correctness,
        avg_runtime_ms=avg_runtime,
        avg_memory_kb=avg_memory,
        avg_ai_score=avg_ai,
        language_distribution=lang_dist,
        difficulty_distribution=diff_dist,
        topic_performance=topic_perf,
        recent_trends=trends,
        improvement_rate=round(improvement, 1),
    )


# ─── Skill Analytics ──────────────────────────────────────────────────────

def _get_skill_analytics(db: Session, user_id: int) -> SkillAnalyticsResponse:
    skills = db.query(SkillAnalytics).filter(SkillAnalytics.user_id == user_id).all()

    items = [
        SkillHeatmapItem(
            skill=s.skill_name,
            category=s.category or "other",
            proficiency=round(s.proficiency_level, 1),
            trend=s.trend or "stable",
            evidence_count=s.evidence_count or 0,
            last_assessed=s.last_assessed,
        )
        for s in skills
    ]

    total = len(items)
    learned = len([i for i in items if i.proficiency >= 40])
    mastered = len([i for i in items if i.proficiency >= 80])
    weak = sorted(items, key=lambda x: x.proficiency)[:5]
    strong = sorted(items, key=lambda x: x.proficiency, reverse=True)[:5]
    improving = [i for i in items if i.trend == "improving"]
    declining = [i for i in items if i.trend == "declining"]

    return SkillAnalyticsResponse(
        total_skills=total,
        skills_learned=learned,
        skills_mastered=mastered,
        weak_skills=weak,
        strong_skills=strong,
        heatmap=items,
        improvement_skills=improving,
        declining_skills=declining,
    )


# ─── Learning Analytics ───────────────────────────────────────────────────

def _get_learning_analytics(db: Session, user_id: int) -> LearningAnalyticsResponse:
    items = db.query(LearningProgress).filter(LearningProgress.user_id == user_id).all()

    total_hours = sum(p.actual_hours or 0 for p in items)
    completed = len([p for p in items if p.status in ("completed", "mastered")])
    in_progress = len([p for p in items if p.status == "in_progress"])
    total = len(items)
    rate = round((completed / total * 100) if total > 0 else 0, 1)

    # Streak
    from datetime import date
    dates = set()
    for p in items:
        if p.completed_at:
            dates.add(p.completed_at.date())
    streak = 0
    d = date.today()
    while d in dates:
        streak += 1
        d -= timedelta(days=1)

    # Daily/weekly/monthly hours
    now = datetime.now(timezone.utc)
    daily = []
    for i in range(7):
        day = now - timedelta(days=i)
        day_start = day.replace(hour=0, minute=0, second=0, microsecond=0)
        day_end = day_start + timedelta(days=1)
        h = sum(p.actual_hours or 0 for p in items if p.completed_at and day_start <= p.completed_at < day_end)
        daily.append(TrendPoint(date=day_start, score=round(h, 1)))
    daily.reverse()

    weekly = []
    for i in range(4):
        week_start = now - timedelta(weeks=i + 1)
        week_end = now - timedelta(weeks=i)
        h = sum(p.actual_hours or 0 for p in items if p.completed_at and week_start <= p.completed_at < week_end)
        weekly.append(TrendPoint(date=week_start, score=round(h, 1)))
    weekly.reverse()

    monthly = []
    for i in range(6):
        month_start = now - timedelta(days=30 * (i + 1))
        month_end = now - timedelta(days=30 * i)
        h = sum(p.actual_hours or 0 for p in items if p.completed_at and month_start <= p.completed_at < month_end)
        monthly.append(TrendPoint(date=month_start, score=round(h, 1)))
    monthly.reverse()

    # Roadmap completion
    roadmap = db.query(LearningRoadmap).filter(
        LearningRoadmap.user_id == user_id,
        LearningRoadmap.status == "active",
    ).first()
    roadmap_pct = roadmap.progress_percentage if roadmap else 0.0

    # Progress trend
    progress_trend = [
        TrendPoint(date=p.completed_at or p.created_at, score=p.progress_percentage or 0)
        for p in items if p.completed_at
    ]
    progress_trend.sort(key=lambda x: x.date)
    progress_trend = progress_trend[-10:]

    return LearningAnalyticsResponse(
        total_hours=round(total_hours, 1),
        completed_topics=completed,
        in_progress_topics=in_progress,
        total_topics=total,
        completion_rate=rate,
        streak_days=streak,
        daily_hours=daily,
        weekly_hours=weekly,
        monthly_hours=monthly,
        roadmap_completion=round(roadmap_pct, 1),
        progress_trend=progress_trend,
    )


# ─── Career Analytics ─────────────────────────────────────────────────────

def _get_career_analytics(db: Session, user_id: int) -> CareerAnalyticsResponse:
    readiness = db.query(CareerReadiness).filter(
        CareerReadiness.user_id == user_id,
    ).order_by(CareerReadiness.created_at.desc()).first()

    overall = readiness.overall_score if readiness else 0.0
    resume_m = (readiness.resume_match_score or 0.0) if readiness else 0.0
    ats = readiness.ats_score if readiness else 0.0
    interview_r = readiness.interview_score if readiness else 0.0
    coding_r = readiness.coding_score if readiness else 0.0
    learning_r = readiness.learning_score if readiness else 0.0
    skill_gap = readiness.skill_gap_score if readiness else 0.0

    # Role readiness
    from app.routes.career import ROLE_SKILL_REQUIREMENTS
    role_readiness = {}
    if readiness:
        resume_skills = set()
        if readiness.resume_analysis_id:
            ra = db.query(ResumeAnalysis).filter(ResumeAnalysis.id == readiness.resume_analysis_id).first()
            if ra and ra.detected_skills:
                resume_skills = set(s.lower().strip() for s in _parse_json_field(ra.detected_skills))
        for role, req_skills in ROLE_SKILL_REQUIREMENTS.items():
            matched = len([s for s in req_skills if s.lower() in resume_skills])
            role_readiness[role] = round((matched / len(req_skills)) * 100) if req_skills else 0

    # Company readiness
    from app.routes.career import COMPANY_REQUIREMENTS
    company_readiness = {}
    if readiness:
        for company, req in COMPANY_REQUIREMENTS.items():
            if resume_m >= req.get("min_score", 0):
                company_readiness[company] = min(100, round(resume_m * 1.1))
            else:
                company_readiness[company] = round(resume_m * 0.8)

    # Readiness trend
    history = db.query(CareerReadinessHistory).filter(
        CareerReadinessHistory.user_id == user_id,
    ).order_by(CareerReadinessHistory.created_at.desc()).limit(20).all()

    trend = [
        TrendPoint(date=h.created_at, score=round(h.overall_score or 0, 1))
        for h in reversed(history)
    ]

    # Improvement
    improvement = 0.0
    if len(history) >= 2:
        old = history[-1].overall_score or 0
        new = history[0].overall_score or 0
        if old > 0:
            improvement = ((new - old) / old) * 100

    return CareerAnalyticsResponse(
        overall_readiness=round(overall, 1),
        resume_match=round(resume_m, 1),
        ats_score=round(ats, 1),
        interview_readiness=round(interview_r, 1),
        coding_readiness=round(coding_r, 1),
        learning_progress=round(learning_r, 1),
        skill_gap_score=round(skill_gap, 1),
        role_readiness=role_readiness,
        company_readiness=company_readiness,
        readiness_trend=trend,
        improvement_rate=round(improvement, 1),
    )


# ─── Topic Analytics ──────────────────────────────────────────────────────

def _get_topic_analytics(db: Session, user_id: int) -> TopicAnalyticsResponse:
    # Interview topics
    raw = db.query(Question.topic, Question.score).join(InterviewSession).filter(
        InterviewSession.user_id == user_id,
        Question.score.isnot(None),
        Question.topic.isnot(None),
    ).all()

    topic_groups = {}
    for topic, score in raw:
        norm = _norm_topic(topic)
        topic_groups.setdefault(norm, []).append(score)

    # Coding topics
    coding_sessions = db.query(CodingSession).filter(CodingSession.user_id == user_id).all()
    for sess in coding_sessions:
        if sess.challenge and sess.challenge.topics:
            for t in sess.challenge.topics:
                topic_groups.setdefault(t, []).append(sess.coding_score or 0)

    all_topics = [
        TopicMetric(topic=t, average_score=round(sum(s) / len(s), 1), question_count=len(s))
        for t, s in topic_groups.items()
    ]

    weak = sorted(all_topics, key=lambda x: x.average_score)[:5]
    strong = sorted(all_topics, key=lambda x: x.average_score, reverse=True)[:5]

    # Topic trends (from performance metrics)
    perf = db.query(PerformanceMetrics).filter(
        PerformanceMetrics.user_id == user_id,
    ).order_by(PerformanceMetrics.created_at.desc()).limit(20).all()

    topic_trends = {}
    for p in perf:
        if p.topic_scores:
            scores = _parse_json_field(p.topic_scores) if isinstance(p.topic_scores, str) else (p.topic_scores or {})
            if isinstance(scores, dict):
                for topic, score in scores.items():
                    norm = _norm_topic(topic)
                    topic_trends.setdefault(norm, []).append(
                        TrendPoint(date=p.created_at, score=float(score))
                    )

    # Improvement/declining
    improving = []
    declining = []
    for t in all_topics:
        trend_data = topic_trends.get(t.topic, [])
        if len(trend_data) >= 2:
            old = trend_data[0].score
            new = trend_data[-1].score
            if new > old + 5:
                improving.append(t)
            elif new < old - 5:
                declining.append(t)

    return TopicAnalyticsResponse(
        topic_scores=all_topics,
        weak_topics=weak,
        strong_topics=strong,
        topic_trends=topic_trends,
        improvement_topics=improving,
        declining_topics=declining,
    )


# ─── Historical Trends ────────────────────────────────────────────────────

def _get_historical_trends(db: Session, user_id: int) -> HistoricalTrendResponse:
    now = datetime.now(timezone.utc)

    # Daily readiness
    daily = []
    for i in range(30):
        day = now - timedelta(days=i)
        day_start = day.replace(hour=0, minute=0, second=0, microsecond=0)
        day_end = day_start + timedelta(days=1)
        h = db.query(CareerReadinessHistory).filter(
            CareerReadinessHistory.user_id == user_id,
            CareerReadinessHistory.created_at >= day_start,
            CareerReadinessHistory.created_at < day_end,
        ).order_by(CareerReadinessHistory.created_at.desc()).first()
        daily.append(TrendPoint(date=day_start, score=round(h.overall_score or 0, 1) if h else 0))
    daily.reverse()

    # Weekly
    weekly = []
    for i in range(12):
        week_start = now - timedelta(weeks=i + 1)
        week_end = now - timedelta(weeks=i)
        h = db.query(CareerReadinessHistory).filter(
            CareerReadinessHistory.user_id == user_id,
            CareerReadinessHistory.created_at >= week_start,
            CareerReadinessHistory.created_at < week_end,
        ).order_by(CareerReadinessHistory.created_at.desc()).first()
        weekly.append(TrendPoint(date=week_start, score=round(h.overall_score or 0, 1) if h else 0))
    weekly.reverse()

    # Monthly
    monthly = []
    for i in range(6):
        month_start = now - timedelta(days=30 * (i + 1))
        month_end = now - timedelta(days=30 * i)
        h = db.query(CareerReadinessHistory).filter(
            CareerReadinessHistory.user_id == user_id,
            CareerReadinessHistory.created_at >= month_start,
            CareerReadinessHistory.created_at < month_end,
        ).order_by(CareerReadinessHistory.created_at.desc()).first()
        monthly.append(TrendPoint(date=month_start, score=round(h.overall_score or 0, 1) if h else 0))
    monthly.reverse()

    # Career timeline
    career_tl = [
        TrendPoint(date=h.created_at, score=round(h.overall_score or 0, 1))
        for h in db.query(CareerReadinessHistory).filter(
            CareerReadinessHistory.user_id == user_id,
        ).order_by(CareerReadinessHistory.created_at.asc()).limit(50).all()
    ]

    # Interview timeline
    interview_tl = [
        TrendPoint(date=s.started_at, score=round(float(s.score), 1))
        for s in db.query(InterviewSession).filter(
            InterviewSession.user_id == user_id,
            InterviewSession.status == "completed",
            InterviewSession.score.isnot(None),
        ).order_by(InterviewSession.started_at.asc()).limit(50).all()
    ]

    # Coding timeline
    coding_tl = [
        TrendPoint(date=s.ended_at or s.started_at, score=round(float(s.coding_score), 1))
        for s in db.query(CodingSession).filter(
            CodingSession.user_id == user_id,
            CodingSession.status == "submitted",
            CodingSession.coding_score.isnot(None),
        ).order_by(CodingSession.started_at.asc()).limit(50).all()
    ]

    # Learning timeline
    learning_tl = [
        TrendPoint(date=p.completed_at, score=p.progress_percentage or 0)
        for p in db.query(LearningProgress).filter(
            LearningProgress.user_id == user_id,
            LearningProgress.completed_at.isnot(None),
        ).order_by(LearningProgress.completed_at.asc()).limit(50).all()
    ]

    return HistoricalTrendResponse(
        daily=daily, weekly=weekly, monthly=monthly,
        career_timeline=career_tl, interview_timeline=interview_tl,
        coding_timeline=coding_tl, learning_timeline=learning_tl,
    )


# ─── Predictions ──────────────────────────────────────────────────────────

def _get_predictions(db: Session, user_id: int) -> PredictionResponse:
    # Gather signals
    interview_avg = db.query(func.avg(InterviewSession.score)).filter(
        InterviewSession.user_id == user_id,
        InterviewSession.status == "completed",
    ).scalar() or 0.0

    coding_avg = db.query(func.avg(CodingSession.coding_score)).filter(
        CodingSession.user_id == user_id,
        CodingSession.status == "submitted",
    ).scalar() or 0.0

    readiness = db.query(CareerReadiness).filter(
        CareerReadiness.user_id == user_id,
    ).order_by(CareerReadiness.created_at.desc()).first()

    learning_items = db.query(LearningProgress).filter(
        LearningProgress.user_id == user_id,
    ).all()
    completed = len([p for p in learning_items if p.status in ("completed", "mastered")])
    total = len(learning_items)

    # Improvement trend
    scores = db.query(InterviewSession.score).filter(
        InterviewSession.user_id == user_id,
        InterviewSession.status == "completed",
        InterviewSession.score.isnot(None),
    ).order_by(InterviewSession.started_at.asc()).all()

    improvement_velocity = 0.0
    if len(scores) >= 3:
        first_half = sum(s.score for s in scores[:len(scores) // 2]) / (len(scores) // 2)
        second_half = sum(s.score for s in scores[len(scores) // 2:]) / (len(scores) - len(scores) // 2)
        improvement_velocity = second_half - first_half

    # Predictions (heuristic ML-inspired)
    readiness_score = readiness.overall_score if readiness else 0.0
    predicted_readiness = min(100, readiness_score + improvement_velocity * 2)

    interview_success = min(100, interview_avg * 10 + improvement_velocity * 5)
    coding_success = min(100, coding_avg + improvement_velocity * 3)

    # Time to target
    target_gap = max(0, 80 - readiness_score)
    weeks_to_target = max(1, int(target_gap / max(1, improvement_velocity * 2))) if improvement_velocity > 0 else "N/A"
    time_str = f"{weeks_to_target} weeks" if isinstance(weeks_to_target, int) else "Needs more data"

    # Learning forecast
    if total > 0 and completed > 0:
        rate = completed / total
        remaining = total - completed
        weeks_left = max(1, int(remaining / max(1, rate * 2)))
        learn_forecast = f"~{weeks_left} weeks at current pace"
    else:
        learn_forecast = "No learning data yet"

    # Interview forecast
    if improvement_velocity > 0:
        interview_forecast = f"+{round(improvement_velocity * 2, 1)} points projected improvement"
    elif interview_avg > 0:
        interview_forecast = "Stable performance — focus on weak topics"
    else:
        interview_forecast = "No interview data yet"

    # Factors
    factors = []
    if readiness_score > 70:
        factors.append("Strong overall readiness")
    if interview_avg > 7:
        factors.append("Above-average interview performance")
    if coding_avg > 70:
        factors.append("Solid coding skills")
    if improvement_velocity > 0.5:
        factors.append("Positive improvement trend")
    if completed > total * 0.5 if total > 0 else False:
        factors.append("Good learning progress")
    if not factors:
        factors.append("Insufficient data — complete more activities")

    confidence = min(100, (len(scores) * 5 + total * 3 + (20 if readiness else 0)))

    return PredictionResponse(
        predicted_readiness=round(predicted_readiness, 1),
        predicted_interview_success=round(interview_success, 1),
        predicted_coding_success=round(coding_success, 1),
        estimated_time_to_target=time_str,
        learning_completion_forecast=learn_forecast,
        interview_improvement_forecast=interview_forecast,
        confidence=round(confidence, 1),
        factors=factors,
    )


# ─── Recommendations ──────────────────────────────────────────────────────

def _get_recommendations(db: Session, user_id: int) -> RecommendationResponse:
    # Next skill from skill gap
    gap = db.query(SkillGapAnalysis).filter(
        SkillGapAnalysis.user_id == user_id,
    ).order_by(SkillGapAnalysis.created_at.desc()).first()

    next_skill = None
    if gap and gap.missing_skills:
        missing = _parse_json_field(gap.missing_skills)
        if missing:
            next_skill = missing[0] if isinstance(missing, list) else str(missing)

    # Next interview topic from weak areas
    interview_weak = db.query(PerformanceMetrics).filter(
        PerformanceMetrics.user_id == user_id,
        PerformanceMetrics.metric_type == "interview",
    ).order_by(PerformanceMetrics.created_at.desc()).first()

    next_interview = None
    if interview_weak and interview_weak.weak_topics:
        weak = _parse_json_field(interview_weak.weak_topics)
        if weak:
            next_interview = weak[0] if isinstance(weak, list) else str(weak)

    # Next coding topic
    coding_weak = db.query(PerformanceMetrics).filter(
        PerformanceMetrics.user_id == user_id,
        PerformanceMetrics.metric_type == "coding",
    ).order_by(PerformanceMetrics.created_at.desc()).first()

    next_coding = None
    if coding_weak and coding_weak.weak_topics:
        weak = _parse_json_field(coding_weak.weak_topics)
        if weak:
            next_coding = weak[0] if isinstance(weak, list) else str(weak)

    # Revision topics (declining skills)
    declining = db.query(SkillAnalytics).filter(
        SkillAnalytics.user_id == user_id,
        SkillAnalytics.trend == "declining",
    ).all()
    revision = [s.skill_name for s in declining[:5]]

    # Priority actions
    priorities = []
    if next_skill:
        priorities.append({"action": f"Learn {next_skill}", "reason": "Missing skill from job requirements", "priority": "high"})
    if next_interview:
        priorities.append({"action": f"Practice {next_interview}", "reason": "Weak interview topic", "priority": "high"})
    if next_coding:
        priorities.append({"action": f"Solve {next_coding} problems", "reason": "Weak coding area", "priority": "medium"})
    if revision:
        priorities.append({"action": f"Review {revision[0]}", "reason": "Declining skill trend", "priority": "medium"})

    # Next mini project suggestion
    next_project = None
    if gap:
        missing = _parse_json_field(gap.missing_skills)
        if missing and len(missing) > 0:
            next_project = f"Build a project using {missing[0]}" if missing else None

    return RecommendationResponse(
        next_skill=next_skill,
        next_interview_topic=next_interview,
        next_coding_topic=next_coding,
        next_mini_project=next_project,
        revision_topics=revision,
        priority_actions=priorities,
    )


# ─── Endpoints ────────────────────────────────────────────────────────────

@router.get("/dashboard", response_model=AnalyticsResponse)
def get_analytics_dashboard(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Full analytics dashboard — returns all sections. Each section is isolated so a crash in one doesn't break the whole dashboard."""
    _empty_trend = lambda: {"average_score": 0.0, "total_interviews": 0, "weak_topics": [], "strong_topics": [], "progress_trends": [], "role_distribution": {}, "avg_accuracy": 0.0, "avg_communication": 0.0, "avg_confidence": 0.0, "avg_completeness": 0.0, "average_response_speed": 0.0, "hesitation_score": 0.0, "pressure_handling": 100.0, "confidence_estimation": 0.0, "improvement_rate": 0.0}

    def _safe(name, fn, *args):
        try:
            return fn(*args)
        except Exception as e:
            print(f"[ANALYTICS] {name} failed for user {current_user.id}: {e}")
            traceback.print_exc()
            return None

    interview = _safe("interview", _get_interview_analytics, db, current_user.id) or _empty_trend()
    coding = _safe("coding", _get_coding_analytics, db, current_user.id)
    skills = _safe("skills", _get_skill_analytics, db, current_user.id)
    learning = _safe("learning", _get_learning_analytics, db, current_user.id)
    career = _safe("career", _get_career_analytics, db, current_user.id)
    topics = _safe("topics", _get_topic_analytics, db, current_user.id)
    history = _safe("history", _get_historical_trends, db, current_user.id)
    predictions = _safe("predictions", _get_predictions, db, current_user.id)
    recommendations = _safe("recommendations", _get_recommendations, db, current_user.id)

    return AnalyticsResponse(
        **interview,
        coding=coding,
        skills=skills,
        learning=learning,
        career=career,
        topics=topics,
        history=history,
        predictions=predictions,
        recommendations=recommendations,
    )


@router.get("/interview")
def get_interview_analytics(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return _get_interview_analytics(db, current_user.id)


@router.get("/coding")
def get_coding_analytics(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return _get_coding_analytics(db, current_user.id)


@router.get("/skills")
def get_skill_analytics(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return _get_skill_analytics(db, current_user.id)


@router.get("/learning")
def get_learning_analytics(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return _get_learning_analytics(db, current_user.id)


@router.get("/career")
def get_career_analytics(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return _get_career_analytics(db, current_user.id)


@router.get("/topics")
def get_topic_analytics(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return _get_topic_analytics(db, current_user.id)


@router.get("/history")
def get_historical_trends(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return _get_historical_trends(db, current_user.id)


@router.get("/predictions")
def get_predictions(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return _get_predictions(db, current_user.id)
