from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.database import Base

class InterviewSession(Base):
    __tablename__ = "interview_sessions"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), index=True)
    job_role_id = Column(Integer, ForeignKey("job_roles.id"), nullable=True)
    job_description_id = Column(Integer, ForeignKey("job_descriptions.id"), nullable=True)
    role = Column(String)  # e.g., "Software Engineer", "Data Scientist"
    difficulty = Column(String, default="Medium")
    interview_type = Column(String, default="Technical")
    status = Column(String, default="pending", index=True)  # e.g., "pending", "in-progress", "completed"
    score = Column(Float, nullable=True)

    # Topic specific scores
    score_dsa = Column(Float, nullable=True)
    score_dbms = Column(Float, nullable=True)
    score_os = Column(Float, nullable=True)
    score_cn = Column(Float, nullable=True)
    score_oop = Column(Float, nullable=True)
    score_system_design = Column(Float, nullable=True)
    score_project = Column(Float, nullable=True)
    score_hr = Column(Float, nullable=True)
    score_communication = Column(Float, nullable=True)

    started_at = Column(DateTime(timezone=True), server_default=func.now())
    ended_at = Column(DateTime(timezone=True), nullable=True)

    user = relationship("User", back_populates="sessions")
    job_role = relationship("JobRole", back_populates="sessions")
    job_description = relationship("JobDescription")
    questions = relationship("Question", back_populates="session")
    metrics = relationship("InterviewQuestionMetric", back_populates="session")
