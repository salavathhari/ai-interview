from sqlalchemy import Column, Integer, String, Text, Float, Boolean, DateTime, ForeignKey, JSON
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.database import Base


class SkillDependency(Base):
    """Maps prerequisite relationships between skills for learning order."""
    __tablename__ = "skill_dependencies"

    id = Column(Integer, primary_key=True, index=True)
    skill_name = Column(String, index=True, nullable=False)
    prerequisite = Column(String, nullable=False)
    dependency_type = Column(String, default="required")  # required/recommended
    description = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class LearningProgress(Base):
    """Tracks per-topic learning progress for each user."""
    __tablename__ = "learning_progress"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), index=True)
    roadmap_id = Column(Integer, ForeignKey("learning_roadmaps.id"), nullable=True)
    topic_name = Column(String, nullable=False)
    skill_name = Column(String, nullable=True)
    status = Column(String, default="not_started")  # not_started/in_progress/completed/mastered
    progress_percentage = Column(Float, default=0.0)
    estimated_hours = Column(Float, nullable=True)
    actual_hours = Column(Float, nullable=True)
    difficulty = Column(String, nullable=True)
    priority = Column(String, nullable=True)  # high/medium/low
    started_at = Column(DateTime(timezone=True), nullable=True)
    completed_at = Column(DateTime(timezone=True), nullable=True)
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    user = relationship("User")
    roadmap = relationship("LearningRoadmap")


class CareerRecommendation(Base):
    """Stores prioritized career recommendations with reasoning."""
    __tablename__ = "career_recommendations"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), index=True)
    recommendation_type = Column(String, nullable=False)  # skill/learning/interview/coding/career
    title = Column(String, nullable=False)
    description = Column(Text, nullable=True)
    priority = Column(String, default="medium")  # critical/high/medium/low
    reason = Column(Text, nullable=True)
    action_url = Column(String, nullable=True)
    is_dismissed = Column(Boolean, default=False)
    is_completed = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    user = relationship("User")


class PerformanceMetrics(Base):
    """Stores aggregated performance data from interviews and coding rounds."""
    __tablename__ = "performance_metrics"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), index=True)
    metric_type = Column(String, nullable=False)  # interview/coding
    session_id = Column(Integer, nullable=True)  # interview_session or coding_session id
    overall_score = Column(Float, nullable=True)
    topic_scores = Column(Text, nullable=True)  # JSON: {"dsa": 80, "dbms": 60, ...}
    weak_topics = Column(Text, nullable=True)  # JSON: ["graphs", "system_design"]
    strong_topics = Column(Text, nullable=True)  # JSON: ["arrays", "oop"]
    difficulty_level = Column(String, nullable=True)
    role = Column(String, nullable=True)
    completed_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    user = relationship("User")


class SkillAnalytics(Base):
    """Aggregated skill analytics for heatmap and progress visualization."""
    __tablename__ = "skill_analytics"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), index=True)
    skill_name = Column(String, nullable=False)
    category = Column(String, nullable=True)  # programming/framework/database/cloud/tool/soft
    proficiency_level = Column(Float, default=0.0)  # 0-100
    source = Column(String, nullable=True)  # resume/interview/coding/learning
    evidence_count = Column(Integer, default=0)
    last_assessed = Column(DateTime(timezone=True), nullable=True)
    trend = Column(String, default="stable")  # improving/declining/stable
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    user = relationship("User")
