from sqlalchemy import Column, Integer, String, Text, Float, Boolean, DateTime, ForeignKey
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.database import Base


class JobDescription(Base):
    __tablename__ = "job_descriptions"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    title = Column(String)
    company = Column(String, nullable=True)
    raw_text = Column(Text)
    source = Column(String)  # pdf/docx/paste
    file_path = Column(String, nullable=True)
    required_skills = Column(Text)  # JSON string
    preferred_skills = Column(Text)  # JSON string
    technologies = Column(Text)  # JSON string
    responsibilities = Column(Text)  # JSON string
    experience_years = Column(String, nullable=True)
    education_requirements = Column(Text, nullable=True)
    soft_skills = Column(Text)  # JSON string
    keywords = Column(Text)  # JSON string
    is_analyzed = Column(Boolean, default=False)
    content_hash = Column(String, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    user = relationship("User", back_populates="job_descriptions")
    resume_analyses = relationship("ResumeAnalysis", back_populates="job_description")
    skill_gap_analyses = relationship("SkillGapAnalysis", back_populates="job_description")


class ResumeAnalysis(Base):
    __tablename__ = "resume_analyses"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), index=True)
    resume_id = Column(Integer, ForeignKey("resumes.id"), index=True)
    job_description_id = Column(Integer, ForeignKey("job_descriptions.id"), nullable=True)
    summary = Column(Text, nullable=True)  # AI-generated summary
    detected_skills = Column(Text)  # JSON string
    experience_level = Column(String, nullable=True)
    projects = Column(Text)  # JSON string
    technologies = Column(Text)  # JSON string
    education = Column(Text)  # JSON string
    certifications = Column(Text)  # JSON string
    ats_score = Column(Float, nullable=True)  # 0-100
    ats_breakdown = Column(Text)  # JSON string - formatting, keywords, etc.
    ats_suggestions = Column(Text)  # JSON string
    resume_match_score = Column(Float, nullable=True)  # 0-100
    match_breakdown = Column(Text)  # JSON string - technical, projects, experience, etc.
    is_analyzed = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    user = relationship("User", back_populates="resume_analyses")
    resume = relationship("Resume")
    job_description = relationship("JobDescription", back_populates="resume_analyses")
    skill_gap_analyses = relationship("SkillGapAnalysis", back_populates="resume_analysis")
    optimized_resumes = relationship("OptimizedResume", back_populates="resume_analysis")
    career_readiness = relationship("CareerReadiness", back_populates="resume_analysis")


class SkillGapAnalysis(Base):
    __tablename__ = "skill_gap_analyses"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), index=True)
    resume_analysis_id = Column(Integer, ForeignKey("resume_analyses.id"))
    job_description_id = Column(Integer, ForeignKey("job_descriptions.id"))
    matched_skills = Column(Text)  # JSON string
    missing_skills = Column(Text)  # JSON string
    additional_skills = Column(Text)  # JSON string
    priority_skills = Column(Text)  # JSON string
    match_percentage = Column(Float, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    user = relationship("User", back_populates="skill_gap_analyses")
    resume_analysis = relationship("ResumeAnalysis", back_populates="skill_gap_analyses")
    job_description = relationship("JobDescription", back_populates="skill_gap_analyses")
    learning_roadmaps = relationship("LearningRoadmap", back_populates="skill_gap")


class LearningRoadmap(Base):
    __tablename__ = "learning_roadmaps"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), index=True)
    skill_gap_id = Column(Integer, ForeignKey("skill_gap_analyses.id"), nullable=True)
    roadmap_items = Column(Text)  # JSON string - legacy flat topic list
    phases = Column(Text)  # JSON string - structured phase list with topics, projects, etc.
    current_phase_index = Column(Integer, default=0)
    daily_plan = Column(Text)  # JSON string - today's learning plan
    mentor_tips = Column(Text)  # JSON string - AI mentor recommendations
    skill_gap_summary = Column(Text)  # JSON string - skill gap overview
    total_hours = Column(Float, nullable=True)
    estimated_weeks = Column(Integer, nullable=True)
    status = Column(String, default="active")  # active/completed/archived
    completed_topics = Column(Text, nullable=True)  # JSON string of completed topic names
    progress_percentage = Column(Float, default=0.0)
    career_goal = Column(String, nullable=True)
    target_role = Column(String, nullable=True)
    target_company = Column(String, nullable=True)
    current_readiness = Column(Float, default=0.0)
    target_readiness = Column(Float, default=85.0)
    interview_readiness = Column(Float, default=0.0)
    coding_readiness = Column(Float, default=0.0)
    version = Column(Integer, default=1)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    user = relationship("User", back_populates="learning_roadmaps")
    skill_gap = relationship("SkillGapAnalysis", back_populates="learning_roadmaps")


class OptimizedResume(Base):
    __tablename__ = "optimized_resumes"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), index=True)
    resume_analysis_id = Column(Integer, ForeignKey("resume_analyses.id"))
    optimized_text = Column(Text)  # full optimized resume text
    improvements = Column(Text)  # JSON string - list of improvements made
    professional_summary = Column(Text, nullable=True)
    optimized_skills = Column(Text)  # JSON string
    optimized_projects = Column(Text)  # JSON string
    optimized_keywords = Column(Text)  # JSON string
    optimized_experience = Column(Text)  # JSON string
    format = Column(String, default="pdf")  # pdf/docx
    file_path = Column(String, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    user = relationship("User", back_populates="optimized_resumes")
    resume_analysis = relationship("ResumeAnalysis", back_populates="optimized_resumes")


class CareerReadiness(Base):
    __tablename__ = "career_readiness"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), index=True)
    resume_analysis_id = Column(Integer, ForeignKey("resume_analyses.id"), nullable=True)
    skill_gap_id = Column(Integer, ForeignKey("skill_gap_analyses.id"), nullable=True)
    resume_match_score = Column(Float, nullable=True)
    ats_score = Column(Float, nullable=True)
    interview_score = Column(Float, nullable=True)
    coding_score = Column(Float, nullable=True)
    skill_gap_score = Column(Float, nullable=True)
    project_score = Column(Float, nullable=True)
    consistency_score = Column(Float, nullable=True)
    learning_score = Column(Float, nullable=True)
    role_match_score = Column(Float, nullable=True)
    company_match_score = Column(Float, nullable=True)
    overall_score = Column(Float, nullable=True)
    score_breakdown = Column(Text, nullable=True)  # JSON: detailed component breakdown
    recommendations = Column(Text)  # JSON string
    ai_suggestions = Column(Text)  # JSON string
    target_role = Column(String, nullable=True)
    target_company = Column(String, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    user = relationship("User", back_populates="career_readiness")
    resume_analysis = relationship("ResumeAnalysis", back_populates="career_readiness")
    skill_gap = relationship("SkillGapAnalysis")


class CareerReadinessHistory(Base):
    """Tracks career readiness score changes over time for trend analysis."""
    __tablename__ = "career_readiness_history"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), index=True)
    overall_score = Column(Float, nullable=True)
    resume_match_score = Column(Float, nullable=True)
    ats_score = Column(Float, nullable=True)
    interview_score = Column(Float, nullable=True)
    coding_score = Column(Float, nullable=True)
    skill_gap_score = Column(Float, nullable=True)
    learning_score = Column(Float, nullable=True)
    trigger_event = Column(String, nullable=True)  # resume_upload/jd_upload/interview/coding/learning/manual
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    user = relationship("User")
