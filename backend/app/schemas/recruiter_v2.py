from pydantic import BaseModel
from typing import List, Optional, Any
from datetime import datetime


# ─── Job Post ────────────────────────────────────────────────────────────────

class JobPostCreate(BaseModel):
    title: str
    description: Optional[str] = None
    requirements: Optional[str] = None
    company_id: Optional[int] = None
    department: Optional[str] = None
    location: Optional[str] = None
    employment_type: Optional[str] = "full_time"
    experience_level: Optional[str] = None
    salary_min: Optional[int] = None
    salary_max: Optional[int] = None
    salary_currency: Optional[str] = "USD"
    required_skills: Optional[List[str]] = []
    preferred_skills: Optional[List[str]] = []
    education: Optional[str] = None
    responsibilities: Optional[List[str]] = []
    benefits: Optional[List[str]] = []
    deadline: Optional[datetime] = None
    interview_template_id: Optional[int] = None
    coding_template_id: Optional[int] = None
    status: Optional[str] = "draft"


class JobPostUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    requirements: Optional[str] = None
    company_id: Optional[int] = None
    department: Optional[str] = None
    location: Optional[str] = None
    employment_type: Optional[str] = None
    experience_level: Optional[str] = None
    salary_min: Optional[int] = None
    salary_max: Optional[int] = None
    salary_currency: Optional[str] = None
    required_skills: Optional[List[str]] = None
    preferred_skills: Optional[List[str]] = None
    education: Optional[str] = None
    responsibilities: Optional[List[str]] = None
    benefits: Optional[List[str]] = None
    deadline: Optional[datetime] = None
    interview_template_id: Optional[int] = None
    coding_template_id: Optional[int] = None
    status: Optional[str] = None


class JobPostResponse(BaseModel):
    id: int
    job_role_id: Optional[int] = None
    recruiter_id: int
    company_id: Optional[int] = None
    company_name: Optional[str] = None
    title: str
    description: Optional[str] = None
    requirements: Optional[str] = None
    department: Optional[str] = None
    location: Optional[str] = None
    employment_type: Optional[str] = None
    experience_level: Optional[str] = None
    salary_min: Optional[int] = None
    salary_max: Optional[int] = None
    salary_currency: Optional[str] = None
    required_skills: Optional[List[str]] = []
    preferred_skills: Optional[List[str]] = []
    education: Optional[str] = None
    responsibilities: Optional[List[str]] = []
    benefits: Optional[List[str]] = []
    deadline: Optional[datetime] = None
    interview_template_id: Optional[int] = None
    coding_template_id: Optional[int] = None
    status: str
    invite_code: Optional[str] = None
    application_count: Optional[int] = 0
    posted_at: Optional[datetime] = None
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class JobPostListResponse(BaseModel):
    jobs: List[JobPostResponse]
    total: int
    page: int
    per_page: int


# ─── Applications ────────────────────────────────────────────────────────────

class ApplicationCreate(BaseModel):
    user_id: int
    resume_id: Optional[int] = None
    cover_letter: Optional[str] = None
    source: Optional[str] = "direct"


class ApplicationStageUpdate(BaseModel):
    status: str
    reason: Optional[str] = None


class ApplicationResponse(BaseModel):
    id: int
    job_post_id: int
    user_id: int
    user_name: Optional[str] = None
    user_email: Optional[str] = None
    status: str
    resume_id: Optional[int] = None
    cover_letter: Optional[str] = None
    source: Optional[str] = None
    ats_score: Optional[float] = None
    resume_match_score: Optional[float] = None
    skill_gap_score: Optional[float] = None
    career_readiness_score: Optional[float] = None
    screening_summary: Optional[str] = None
    matched_skills: Optional[List[str]] = []
    missing_skills: Optional[List[str]] = []
    experience_match: Optional[float] = None
    education_match: Optional[float] = None
    interview_score: Optional[float] = None
    coding_score: Optional[float] = None
    final_composite_score: Optional[float] = None
    hiring_recommendation: Optional[str] = None
    strengths: Optional[List[str]] = []
    weaknesses: Optional[List[str]] = []
    decision: Optional[str] = None
    decision_at: Optional[datetime] = None
    decision_reason: Optional[str] = None
    applied_at: datetime
    screened_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class ApplicationListResponse(BaseModel):
    applications: List[ApplicationResponse]
    total: int
    page: int
    per_page: int
    stage_counts: Optional[dict] = None


class ApplicationHistoryResponse(BaseModel):
    id: int
    application_id: int
    from_stage: Optional[str] = None
    to_stage: str
    reason: Optional[str] = None
    recruiter_id: int
    recruiter_name: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True


# ─── Candidate Profile ──────────────────────────────────────────────────────

class CandidateProfileResponse(BaseModel):
    user_id: int
    name: Optional[str] = None
    email: Optional[str] = None
    resume: Optional[dict] = None
    resume_analysis: Optional[dict] = None
    interview_scores: Optional[List[dict]] = []
    coding_scores: Optional[List[dict]] = []
    career_readiness: Optional[dict] = None
    skill_gap: Optional[dict] = None
    applications: Optional[List[dict]] = []
    learning_progress: Optional[dict] = None


# ─── Shortlisting ───────────────────────────────────────────────────────────

class ShortlistAction(BaseModel):
    action: str  # shortlist/reject/hold
    reason: Optional[str] = None
    comments: Optional[str] = None


class ShortlistResponse(BaseModel):
    id: int
    application_id: int
    recruiter_id: int
    action: str
    reason: Optional[str] = None
    comments: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True


# ─── Offers ─────────────────────────────────────────────────────────────────

class OfferCreate(BaseModel):
    salary_offered: Optional[int] = None
    currency: Optional[str] = "USD"
    benefits: Optional[List[str]] = []
    notes: Optional[str] = None
    expires_at: Optional[datetime] = None


class OfferResponse(BaseModel):
    id: int
    application_id: int
    recruiter_id: int
    candidate_name: Optional[str] = None
    job_title: Optional[str] = None
    salary_offered: Optional[int] = None
    currency: Optional[str] = None
    benefits: Optional[List[str]] = []
    status: str
    notes: Optional[str] = None
    expires_at: Optional[datetime] = None
    responded_at: Optional[datetime] = None
    created_at: datetime

    class Config:
        from_attributes = True


# ─── Templates ──────────────────────────────────────────────────────────────

class InterviewTemplateCreate(BaseModel):
    name: str
    description: Optional[str] = None
    role: str
    difficulty: Optional[str] = "Medium"
    interview_type: Optional[str] = "Technical"
    topics: Optional[List[str]] = []
    num_questions: Optional[int] = 5
    time_limit_min: Optional[int] = 30


class InterviewTemplateUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    role: Optional[str] = None
    difficulty: Optional[str] = None
    interview_type: Optional[str] = None
    topics: Optional[List[str]] = None
    num_questions: Optional[int] = None
    time_limit_min: Optional[int] = None
    is_active: Optional[bool] = None


class InterviewTemplateResponse(BaseModel):
    id: int
    recruiter_id: int
    name: str
    description: Optional[str] = None
    role: str
    difficulty: str
    interview_type: str
    topics: Optional[List[str]] = []
    num_questions: int
    time_limit_min: int
    is_active: bool
    created_at: datetime

    class Config:
        from_attributes = True


class CodingTemplateCreate(BaseModel):
    name: str
    description: Optional[str] = None
    difficulty: Optional[str] = "Medium"
    challenge_ids: Optional[List[int]] = []
    time_limit_min: Optional[int] = 60


class CodingTemplateUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    difficulty: Optional[str] = None
    challenge_ids: Optional[List[int]] = None
    time_limit_min: Optional[int] = None
    is_active: Optional[bool] = None


class CodingTemplateResponse(BaseModel):
    id: int
    recruiter_id: int
    name: str
    description: Optional[str] = None
    difficulty: str
    challenge_ids: Optional[List[int]] = []
    time_limit_min: int
    is_active: bool
    created_at: datetime

    class Config:
        from_attributes = True


# ─── Dashboard ──────────────────────────────────────────────────────────────

class RecruiterDashboardV2(BaseModel):
    total_jobs: int
    open_jobs: int
    closed_jobs: int
    draft_jobs: int
    total_applications: int
    applications_in_screening: int
    applications_in_interview: int
    applications_in_coding: int
    shortlisted: int
    rejected: int
    offers_released: int
    hired: int
    avg_candidate_score: Optional[float] = None
    avg_ats_score: Optional[float] = None
    avg_career_readiness: Optional[float] = None
    pipeline: Optional[List[dict]] = []
    recent_activities: Optional[List[dict]] = []
    top_candidates: Optional[List[dict]] = []


# ─── Analytics ──────────────────────────────────────────────────────────────

class RecruiterAnalytics(BaseModel):
    applications_per_job: Optional[List[dict]] = []
    hiring_funnel: Optional[dict] = {}
    avg_scores: Optional[dict] = {}
    time_to_hire_avg: Optional[float] = None
    acceptance_rate: Optional[float] = None
    offer_rate: Optional[float] = None
    top_skills: Optional[List[dict]] = []
    source_breakdown: Optional[List[dict]] = []
    monthly_trend: Optional[List[dict]] = []


# ─── Comparison ─────────────────────────────────────────────────────────────

class CandidateComparison(BaseModel):
    candidates: List[dict]
    rankings: Optional[dict] = {}


# ─── Notifications ──────────────────────────────────────────────────────────

class RecruiterNotificationResponse(BaseModel):
    id: int
    title: Optional[str] = None
    message: Optional[str] = None
    type: Optional[str] = "info"
    is_read: bool
    created_at: datetime

    class Config:
        from_attributes = True


# ─── Activity ───────────────────────────────────────────────────────────────

class RecruiterActivityResponse(BaseModel):
    id: int
    action: str
    target_type: Optional[str] = None
    target_id: Optional[int] = None
    details: Optional[dict] = None
    created_at: datetime

    class Config:
        from_attributes = True


# ─── Candidate Job Board ────────────────────────────────────────────────────

class CandidateJobResponse(BaseModel):
    id: int
    title: str
    description: Optional[str] = None
    company_name: Optional[str] = None
    company_logo: Optional[str] = None
    department: Optional[str] = None
    location: Optional[str] = None
    employment_type: Optional[str] = None
    experience_level: Optional[str] = None
    salary_min: Optional[int] = None
    salary_max: Optional[int] = None
    salary_currency: Optional[str] = None
    required_skills: Optional[List[str]] = []
    preferred_skills: Optional[List[str]] = []
    education: Optional[str] = None
    responsibilities: Optional[List[str]] = []
    benefits: Optional[List[str]] = []
    deadline: Optional[datetime] = None
    posted_at: Optional[datetime] = None
    created_at: datetime
    has_applied: Optional[bool] = False
    ats_estimate: Optional[float] = None
    readiness_match: Optional[float] = None

    class Config:
        from_attributes = True


# ─── Candidate Application ─────────────────────────────────────────────────

class ApplicationSubmit(BaseModel):
    resume_id: int
    cover_letter: Optional[str] = None
    source: Optional[str] = "direct"


class ApplicationTimelineEntry(BaseModel):
    stage: str
    label: str
    timestamp: Optional[datetime] = None
    actor: Optional[str] = None
    note: Optional[str] = None
    is_current: bool = False


class CandidateApplicationResponse(BaseModel):
    id: int
    job_title: str
    company_name: Optional[str] = None
    status: str
    applied_at: datetime
    updated_at: Optional[datetime] = None
    timeline: Optional[List[ApplicationTimelineEntry]] = []
    ats_score: Optional[float] = None
    resume_match_score: Optional[float] = None
    career_readiness_score: Optional[float] = None
    interview_score: Optional[float] = None
    coding_score: Optional[float] = None
    decision: Optional[str] = None
    decision_reason: Optional[str] = None
    offer: Optional[dict] = None

    class Config:
        from_attributes = True


# ─── Application Notes ─────────────────────────────────────────────────────

class ApplicationNoteCreate(BaseModel):
    note: str
    is_internal: Optional[bool] = True


class ApplicationNoteResponse(BaseModel):
    id: int
    application_id: int
    recruiter_id: int
    recruiter_name: Optional[str] = None
    note: str
    is_internal: bool
    created_at: datetime

    class Config:
        from_attributes = True


# ─── Assignments ────────────────────────────────────────────────────────────

class AssignmentCreate(BaseModel):
    assignment_type: str  # interview/coding
    template_id: Optional[int] = None
    due_date: Optional[datetime] = None
    notes: Optional[str] = None


class AssignmentResponse(BaseModel):
    id: int
    application_id: int
    assignment_type: str
    template_id: Optional[int] = None
    assigned_by: int
    assigned_to: int
    status: str
    due_date: Optional[datetime] = None
    notes: Optional[str] = None
    created_at: datetime
    completed_at: Optional[datetime] = None

    class Config:
        from_attributes = True


# ─── Company ────────────────────────────────────────────────────────────────

class CompanyCreate(BaseModel):
    name: str
    description: Optional[str] = None
    website: Optional[str] = None
    logo_url: Optional[str] = None
    industry: Optional[str] = None
    size: Optional[str] = None
    location: Optional[str] = None


class CompanyResponse(BaseModel):
    id: int
    name: str
    description: Optional[str] = None
    website: Optional[str] = None
    logo_url: Optional[str] = None
    industry: Optional[str] = None
    size: Optional[str] = None
    location: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True


# ─── Recruiter Decision ────────────────────────────────────────────────────

class RecruiterDecision(BaseModel):
    decision: str  # shortlisted/rejected/hold/offer_released/hired
    reason: Optional[str] = None
    notes: Optional[str] = None


class FinalEvaluation(BaseModel):
    final_interview_score: Optional[float] = None
    final_coding_score: Optional[float] = None
    final_composite_score: Optional[float] = None
    hiring_recommendation: Optional[str] = None
    strengths: Optional[List[str]] = []
    weaknesses: Optional[List[str]] = []
