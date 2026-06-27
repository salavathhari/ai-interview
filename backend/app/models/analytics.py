"""Analytics Engine — event collection, aggregation, and BI models."""

from sqlalchemy import Column, Integer, String, Text, Float, Boolean, DateTime, ForeignKey, Index
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.database import Base


class AnalyticsEvent(Base):
    """Raw event log — every user action across all modules."""
    __tablename__ = "analytics_events"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), index=True, nullable=False)
    event_type = Column(String(50), nullable=False, index=True)
    event_category = Column(String(30), nullable=False, index=True)
    entity_type = Column(String(30), nullable=True)
    entity_id = Column(Integer, nullable=True)
    metrics_json = Column(Text, nullable=True)
    metadata_json = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), index=True)

    user = relationship("User")

    __table_args__ = (
        Index("ix_analytics_events_user_type", "user_id", "event_type"),
        Index("ix_analytics_events_user_category", "user_id", "event_category"),
        Index("ix_analytics_events_created", "created_at"),
    )


class AnalyticsSummary(Base):
    """Pre-aggregated analytics summaries — refreshed on each event."""
    __tablename__ = "analytics_summary"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), index=True, unique=True, nullable=False)
    total_interviews = Column(Integer, default=0)
    completed_interviews = Column(Integer, default=0)
    avg_interview_score = Column(Float, default=0.0)
    total_coding_sessions = Column(Integer, default=0)
    total_submissions = Column(Integer, default=0)
    avg_correctness = Column(Float, default=0.0)
    avg_coding_score = Column(Float, default=0.0)
    total_learning_hours = Column(Float, default=0.0)
    completed_topics = Column(Integer, default=0)
    total_topics = Column(Integer, default=0)
    learning_streak_days = Column(Integer, default=0)
    skills_learned = Column(Integer, default=0)
    skills_mastered = Column(Integer, default=0)
    career_readiness_score = Column(Float, default=0.0)
    ats_score = Column(Float, default=0.0)
    resume_match_score = Column(Float, default=0.0)
    skill_gap_score = Column(Float, default=0.0)
    last_interview_at = Column(DateTime(timezone=True), nullable=True)
    last_coding_at = Column(DateTime(timezone=True), nullable=True)
    last_learning_at = Column(DateTime(timezone=True), nullable=True)
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    user = relationship("User")
