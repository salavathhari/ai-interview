from sqlalchemy import Column, Integer, String, Text, Float, Boolean, DateTime, ForeignKey, JSON, UniqueConstraint
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.database import Base
from app.models.user import User


class Company(Base):
    """Company profile for recruiter job postings."""
    __tablename__ = "companies"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(200), nullable=False)
    description = Column(Text, nullable=True)
    website = Column(String(500), nullable=True)
    logo_url = Column(String(500), nullable=True)
    industry = Column(String(100), nullable=True)
    size = Column(String(50), nullable=True)  # 1-10/11-50/51-200/201-500/501-1000/1001+
    location = Column(String(200), nullable=True)
    recruiter_id = Column(Integer, ForeignKey("users.id"), index=True)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    recruiter = relationship("User")
    jobs = relationship("RecruiterJobPost", back_populates="company")


class RecruiterJobPost(Base):
    """Extended job posting with full ATS fields. References JobRole for backward compat."""
    __tablename__ = "recruiter_job_posts"

    id = Column(Integer, primary_key=True, index=True)
    job_role_id = Column(Integer, ForeignKey("job_roles.id"), nullable=True)
    recruiter_id = Column(Integer, ForeignKey("users.id"), index=True)
    company_id = Column(Integer, ForeignKey("companies.id"), nullable=True, index=True)
    title = Column(String(300), nullable=False)
    description = Column(Text, nullable=True)
    department = Column(String(100), nullable=True)
    location = Column(String(200), nullable=True)
    employment_type = Column(String(50), default="full_time")
    experience_level = Column(String(50), nullable=True)
    salary_min = Column(Integer, nullable=True)
    salary_max = Column(Integer, nullable=True)
    salary_currency = Column(String(10), default="USD")
    required_skills = Column(JSON, default=list)
    preferred_skills = Column(JSON, default=list)
    education = Column(String(200), nullable=True)
    responsibilities = Column(JSON, default=list)
    benefits = Column(JSON, default=list)
    deadline = Column(DateTime(timezone=True), nullable=True)
    interview_template_id = Column(Integer, nullable=True)
    coding_template_id = Column(Integer, nullable=True)
    status = Column(String(20), default="draft")
    posted_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    job_role = relationship("JobRole")
    recruiter = relationship("User")
    company = relationship("Company", back_populates="jobs")
    applications = relationship("Application", back_populates="job_post", cascade="all, delete-orphan")


class Application(Base):
    """Candidate application — the central connector between candidate and recruiter."""
    __tablename__ = "applications"
    __table_args__ = (
        UniqueConstraint("job_post_id", "user_id", name="uq_application_per_job"),
    )

    id = Column(Integer, primary_key=True, index=True)
    job_post_id = Column(Integer, ForeignKey("recruiter_job_posts.id"), index=True)
    user_id = Column(Integer, ForeignKey("users.id"), index=True)
    recruiter_id = Column(Integer, ForeignKey("users.id"), nullable=True, index=True)
    status = Column(String(30), default="applied")
    resume_id = Column(Integer, ForeignKey("resumes.id"), nullable=True)
    cover_letter = Column(Text, nullable=True)
    source = Column(String(50), nullable=True)

    # ── AI Screening Snapshot (auto-populated on apply) ──
    resume_analysis_id = Column(Integer, ForeignKey("resume_analyses.id"), nullable=True)
    ats_score = Column(Float, nullable=True)
    resume_match_score = Column(Float, nullable=True)
    skill_gap_score = Column(Float, nullable=True)
    career_readiness_score = Column(Float, nullable=True)
    screening_summary = Column(Text, nullable=True)
    matched_skills = Column(JSON, default=list)
    missing_skills = Column(JSON, default=list)
    experience_match = Column(Float, nullable=True)
    education_match = Column(Float, nullable=True)

    # ── Assignment References ──
    interview_session_id = Column(Integer, ForeignKey("interview_sessions.id"), nullable=True)
    coding_session_id = Column(Integer, ForeignKey("coding_sessions.id"), nullable=True)

    # ── Final Evaluation ──
    final_interview_score = Column(Float, nullable=True)
    final_coding_score = Column(Float, nullable=True)
    final_composite_score = Column(Float, nullable=True)
    hiring_recommendation = Column(Text, nullable=True)
    strengths = Column(JSON, default=list)
    weaknesses = Column(JSON, default=list)

    # ── Recruiter Decision ──
    decision = Column(String(30), nullable=True)  # shortlisted/rejected/hold/offer_released/hired
    decision_at = Column(DateTime(timezone=True), nullable=True)
    decision_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    decision_reason = Column(Text, nullable=True)

    # ── Timestamps ──
    applied_at = Column(DateTime(timezone=True), server_default=func.now())
    screened_at = Column(DateTime(timezone=True), nullable=True)
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    job_post = relationship("RecruiterJobPost", back_populates="applications")
    user = relationship("User", foreign_keys=[user_id])
    recruiter_user = relationship("User", foreign_keys=[recruiter_id])
    resume = relationship("Resume")
    resume_analysis = relationship("ResumeAnalysis")
    interview_session = relationship("InterviewSession")
    coding_session = relationship("CodingSession")
    history = relationship("ApplicationHistory", back_populates="application", cascade="all, delete-orphan")
    shortlists = relationship("Shortlist", back_populates="application", cascade="all, delete-orphan")
    offers = relationship("Offer", back_populates="application", cascade="all, delete-orphan")
    notes = relationship("ApplicationNote", back_populates="application", cascade="all, delete-orphan")
    assignments = relationship("CandidateAssignment", back_populates="application", cascade="all, delete-orphan")


class ApplicationHistory(Base):
    """Audit trail of pipeline stage transitions."""
    __tablename__ = "application_history"

    id = Column(Integer, primary_key=True, index=True)
    application_id = Column(Integer, ForeignKey("applications.id"), index=True)
    from_stage = Column(String(30), nullable=True)
    to_stage = Column(String(30))
    reason = Column(Text, nullable=True)
    actor_id = Column(Integer, ForeignKey("users.id"))
    actor_role = Column(String(20), nullable=True)  # candidate/recruiter/system
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    application = relationship("Application", back_populates="history")
    actor = relationship("User", foreign_keys=[actor_id])


class ApplicationNote(Base):
    """Recruiter notes on applications."""
    __tablename__ = "application_notes"

    id = Column(Integer, primary_key=True, index=True)
    application_id = Column(Integer, ForeignKey("applications.id"), index=True)
    recruiter_id = Column(Integer, ForeignKey("users.id"))
    note = Column(Text, nullable=False)
    is_internal = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    application = relationship("Application", back_populates="notes")
    recruiter = relationship("User")


class CandidateAssignment(Base):
    """Tracks interview/coding assignments from recruiter to candidate."""
    __tablename__ = "candidate_assignments"

    id = Column(Integer, primary_key=True, index=True)
    application_id = Column(Integer, ForeignKey("applications.id"), index=True)
    assignment_type = Column(String(20))  # interview/coding
    template_id = Column(Integer, nullable=True)
    assigned_by = Column(Integer, ForeignKey("users.id"))
    assigned_to = Column(Integer, ForeignKey("users.id"), index=True)
    status = Column(String(20), default="pending")  # pending/in_progress/completed/expired
    due_date = Column(DateTime(timezone=True), nullable=True)
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    completed_at = Column(DateTime(timezone=True), nullable=True)

    application = relationship("Application", back_populates="assignments")
    assigner = relationship("User", foreign_keys=[assigned_by])
    candidate = relationship("User", foreign_keys=[assigned_to])


class Shortlist(Base):
    """Recruiter shortlisting/rejection decisions."""
    __tablename__ = "shortlists"

    id = Column(Integer, primary_key=True, index=True)
    application_id = Column(Integer, ForeignKey("applications.id"), index=True)
    recruiter_id = Column(Integer, ForeignKey("users.id"))
    action = Column(String(20))
    reason = Column(Text, nullable=True)
    comments = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    application = relationship("Application", back_populates="shortlists")
    recruiter = relationship("User")


class Offer(Base):
    """Job offers extended from application."""
    __tablename__ = "offers"

    id = Column(Integer, primary_key=True, index=True)
    application_id = Column(Integer, ForeignKey("applications.id"), index=True)
    recruiter_id = Column(Integer, ForeignKey("users.id"))
    salary_offered = Column(Integer, nullable=True)
    currency = Column(String(10), default="USD")
    benefits = Column(JSON, default=list)
    position_title = Column(String(200), nullable=True)
    start_date = Column(DateTime(timezone=True), nullable=True)
    status = Column(String(20), default="pending")
    notes = Column(Text, nullable=True)
    expires_at = Column(DateTime(timezone=True), nullable=True)
    responded_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    application = relationship("Application", back_populates="offers")
    recruiter = relationship("User")


class RecruiterActivity(Base):
    """Audit log for all recruiter actions."""
    __tablename__ = "recruiter_activities"

    id = Column(Integer, primary_key=True, index=True)
    recruiter_id = Column(Integer, ForeignKey("users.id"), index=True)
    action = Column(String(50))
    target_type = Column(String(30))
    target_id = Column(Integer)
    details = Column(JSON, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    recruiter = relationship("User")


class InterviewTemplate(Base):
    """Reusable interview configurations for recruiter jobs."""
    __tablename__ = "interview_templates"

    id = Column(Integer, primary_key=True, index=True)
    recruiter_id = Column(Integer, ForeignKey("users.id"), index=True)
    name = Column(String(200))
    description = Column(Text, nullable=True)
    role = Column(String(100))
    difficulty = Column(String(20), default="Medium")
    interview_type = Column(String(30), default="Technical")
    topics = Column(JSON, default=list)
    num_questions = Column(Integer, default=5)
    time_limit_min = Column(Integer, default=30)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    recruiter = relationship("User")


class CodingTemplate(Base):
    """Reusable coding assessment configurations."""
    __tablename__ = "coding_templates"

    id = Column(Integer, primary_key=True, index=True)
    recruiter_id = Column(Integer, ForeignKey("users.id"), index=True)
    name = Column(String(200))
    description = Column(Text, nullable=True)
    difficulty = Column(String(20), default="Medium")
    challenge_ids = Column(JSON, default=list)
    time_limit_min = Column(Integer, default=60)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    recruiter = relationship("User")
