from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.database import Base

class InterviewQuestionMetric(Base):
    __tablename__ = "interview_question_metrics"

    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(Integer, ForeignKey("interview_sessions.id"))
    question_id = Column(Integer, ForeignKey("questions.id"))

    time_taken = Column(Integer, nullable=True)
    time_limit = Column(Integer, nullable=True)
    evaluation_time = Column(Integer, nullable=True)
    pause_duration = Column(Integer, nullable=True)
    was_auto_submitted = Column(Boolean, default=False)
    warning_triggered = Column(Boolean, default=False)
    difficulty = Column(String, nullable=True)

    question_start_time = Column(DateTime(timezone=True), nullable=True)
    question_end_time = Column(DateTime(timezone=True), nullable=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now())

    session = relationship("InterviewSession", back_populates="metrics")
    question = relationship("Question", back_populates="metrics")
