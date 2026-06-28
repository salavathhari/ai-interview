from sqlalchemy import Column, Integer, String, Boolean, DateTime
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.database import Base
from app.core.encryption import EncryptedString

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(EncryptedString(200))
    email = Column(String(320), unique=True, index=True)  # NOT encrypted — used for login lookups
    hashed_password = Column(String(500))  # NOT encrypted — already hashed
    is_active = Column(Boolean, default=True)
    is_admin = Column(Boolean, default=False)
    is_recruiter = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    sessions = relationship("InterviewSession", back_populates="user")
    resumes = relationship("Resume", back_populates="user")
    job_descriptions = relationship("JobDescription", back_populates="user")
    resume_analyses = relationship("ResumeAnalysis", back_populates="user")
    skill_gap_analyses = relationship("SkillGapAnalysis", back_populates="user")
    learning_roadmaps = relationship("LearningRoadmap", back_populates="user")
    optimized_resumes = relationship("OptimizedResume", back_populates="user")
    career_readiness = relationship("CareerReadiness", back_populates="user")
