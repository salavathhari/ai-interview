from sqlalchemy import Column, Integer, String, Text, Float, Boolean, DateTime, ForeignKey
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.database import Base


class ATSReport(Base):
    __tablename__ = "ats_reports"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    resume_id = Column(Integer, ForeignKey("resumes.id"), nullable=True)
    job_description_id = Column(Integer, ForeignKey("job_descriptions.id"), nullable=True)
    resume_analysis_id = Column(Integer, ForeignKey("resume_analyses.id"), nullable=True)

    overall_score = Column(Float, default=0.0)

    # Score breakdown
    keyword_score = Column(Float, default=0.0)
    skills_score = Column(Float, default=0.0)
    experience_score = Column(Float, default=0.0)
    projects_score = Column(Float, default=0.0)
    education_score = Column(Float, default=0.0)
    formatting_score = Column(Float, default=0.0)
    readability_score = Column(Float, default=0.0)

    # Detailed analysis (JSON strings)
    resume_parsed = Column(Text, nullable=True)
    jd_parsed = Column(Text, nullable=True)
    keyword_analysis = Column(Text, nullable=True)
    formatting_analysis = Column(Text, nullable=True)
    experience_analysis = Column(Text, nullable=True)
    projects_analysis = Column(Text, nullable=True)
    education_analysis = Column(Text, nullable=True)
    readability_analysis = Column(Text, nullable=True)
    matched_skills = Column(Text, nullable=True)
    missing_skills = Column(Text, nullable=True)
    additional_skills = Column(Text, nullable=True)
    recommendations = Column(Text, nullable=True)
    optimization_summary = Column(Text, nullable=True)

    is_analyzed = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    user = relationship("User")
    resume = relationship("Resume")
    job_description = relationship("JobDescription")
