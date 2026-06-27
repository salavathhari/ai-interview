from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime


class JobDescriptionCreate(BaseModel):
    title: str
    company: Optional[str] = None
    raw_text: str
    source: str = "paste"


class JobDescriptionResponse(BaseModel):
    id: int
    user_id: int
    title: str
    company: Optional[str]
    raw_text: str
    source: str
    file_path: Optional[str]
    required_skills: Optional[str]
    preferred_skills: Optional[str]
    technologies: Optional[str]
    responsibilities: Optional[str]
    experience_years: Optional[str]
    education_requirements: Optional[str]
    soft_skills: Optional[str]
    keywords: Optional[str]
    is_analyzed: bool
    content_hash: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True


class JobDescriptionAnalysisResponse(BaseModel):
    job_description: JobDescriptionResponse
    required_skills: List[str]
    preferred_skills: List[str]
    technologies: List[str]
    responsibilities: List[str]
    experience_years: Optional[str]
    education_requirements: Optional[str]
    soft_skills: List[str]
    keywords: List[str]


class ResumeAnalysisResponse(BaseModel):
    id: int
    user_id: int
    resume_id: int
    job_description_id: Optional[int]
    summary: Optional[str]
    detected_skills: Optional[str]
    experience_level: Optional[str]
    projects: Optional[str]
    technologies: Optional[str]
    education: Optional[str]
    certifications: Optional[str]
    ats_score: Optional[float]
    ats_breakdown: Optional[str]
    ats_suggestions: Optional[str]
    resume_match_score: Optional[float]
    match_breakdown: Optional[str]
    is_analyzed: bool
    created_at: datetime

    class Config:
        from_attributes = True


class SkillGapResponse(BaseModel):
    id: int
    user_id: int
    resume_analysis_id: Optional[int]
    job_description_id: Optional[int]
    matched_skills: Optional[str]
    missing_skills: Optional[str]
    additional_skills: Optional[str]
    priority_skills: Optional[str]
    match_percentage: Optional[float]
    created_at: datetime

    class Config:
        from_attributes = True


class RoadmapItem(BaseModel):
    topic: str
    description: str
    hours: float
    difficulty: str
    priority: str
    milestones: List[str]
    mini_project: Optional[str]


class LearningRoadmapResponse(BaseModel):
    id: int
    user_id: int
    skill_gap_id: Optional[int] = None
    roadmap_items: Optional[str] = None
    phases: Optional[str] = None
    current_phase_index: Optional[int] = 0
    daily_plan: Optional[str] = None
    mentor_tips: Optional[str] = None
    skill_gap_summary: Optional[str] = None
    total_hours: Optional[float] = None
    estimated_weeks: Optional[int] = None
    status: str
    completed_topics: Optional[str] = None
    progress_percentage: Optional[float] = 0.0
    career_goal: Optional[str] = None
    target_role: Optional[str] = None
    target_company: Optional[str] = None
    current_readiness: Optional[float] = 0.0
    target_readiness: Optional[float] = 85.0
    interview_readiness: Optional[float] = 0.0
    coding_readiness: Optional[float] = 0.0
    version: Optional[int] = 1
    created_at: datetime

    class Config:
        from_attributes = True


class OptimizedResumeResponse(BaseModel):
    id: int
    user_id: int
    resume_analysis_id: int
    optimized_text: Optional[str]
    improvements: Optional[str]
    professional_summary: Optional[str]
    optimized_skills: Optional[str]
    optimized_projects: Optional[str]
    optimized_keywords: Optional[str]
    optimized_experience: Optional[str]
    format: str
    file_path: Optional[str]
    created_at: datetime

    class Config:
        from_attributes = True


class CareerReadinessResponse(BaseModel):
    id: int
    user_id: int
    resume_analysis_id: Optional[int]
    skill_gap_id: Optional[int]
    resume_match_score: Optional[float]
    ats_score: Optional[float]
    interview_score: Optional[float]
    coding_score: Optional[float]
    skill_gap_score: Optional[float]
    project_score: Optional[float] = None
    consistency_score: Optional[float] = None
    learning_score: Optional[float] = None
    role_match_score: Optional[float] = None
    company_match_score: Optional[float] = None
    overall_score: Optional[float]
    score_breakdown: Optional[str] = None
    recommendations: Optional[str]
    ai_suggestions: Optional[str]
    target_role: Optional[str] = None
    target_company: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True


class CareerReadinessHistoryResponse(BaseModel):
    id: int
    overall_score: Optional[float]
    resume_match_score: Optional[float]
    ats_score: Optional[float]
    interview_score: Optional[float]
    coding_score: Optional[float]
    skill_gap_score: Optional[float]
    learning_score: Optional[float]
    trigger_event: Optional[str]
    created_at: datetime

    class Config:
        from_attributes = True


class RoleReadinessResponse(BaseModel):
    role: str
    readiness_score: float
    matched_skills: List[str]
    missing_skills: List[str]
    recommendations: List[str]


class CompanyReadinessResponse(BaseModel):
    company: str
    readiness_score: float
    matched_skills: List[str]
    missing_skills: List[str]
    recommendations: List[str]


class CareerDashboardResponse(BaseModel):
    resume_match_score: Optional[float]
    ats_score: Optional[float]
    career_readiness: Optional[float]
    interview_readiness: Optional[float]
    coding_readiness: Optional[float]
    missing_skills: List[str]
    recent_analyses: List[ResumeAnalysisResponse]
    skill_gap: Optional[SkillGapResponse]
    roadmap: Optional[LearningRoadmapResponse]
    recommendations: List[str]
    ai_suggestions: List[str]
    resume_match_trend: List[dict]
    interview_trend: List[dict]
    coding_trend: List[dict]


class ATSOptimizeRequest(BaseModel):
    resume_analysis_id: int
    job_description_id: Optional[int] = None


class AnalyzeResumeRequest(BaseModel):
    resume_id: int
    job_description_id: Optional[int] = None


# ── Intelligence Layer Schemas ──

class SkillClassified(BaseModel):
    skill: str
    priority: Optional[str] = "medium"
    reason: Optional[str] = ""
    source: Optional[str] = ""
    current_score: Optional[float] = None
    interview_score: Optional[float] = None
    resume_present: Optional[bool] = None
    related_to: Optional[List[str]] = None


class LearningPathItem(BaseModel):
    skill: str
    order: int
    prerequisites: List[str]
    dependents: List[str]
    difficulty: str
    estimated_hours: float


class SkillGapAnalysisResult(BaseModel):
    match_percentage: Optional[float]
    existing_skills: List[SkillClassified]
    missing_skills: List[SkillClassified]
    weak_skills: List[SkillClassified]
    strong_skills: List[SkillClassified]
    unused_skills: List[SkillClassified]
    transferable_skills: List[SkillClassified]
    learning_path: List[LearningPathItem]
    recommendations: List[dict]
    analyzed_at: str


class LearningProgressResponse(BaseModel):
    id: int
    roadmap_id: Optional[int]
    topic_name: str
    skill_name: Optional[str]
    status: str
    progress_percentage: float
    estimated_hours: Optional[float]
    actual_hours: Optional[float]
    difficulty: Optional[str]
    priority: Optional[str]
    started_at: Optional[str]
    completed_at: Optional[str]
    notes: Optional[str]

    class Config:
        from_attributes = True


class LearningStatsResponse(BaseModel):
    total_topics: int
    completed: int
    in_progress: int
    not_started: int
    mastered: int
    total_hours_learned: float
    estimated_hours: float
    learning_velocity_per_week: float
    completion_rate: float


class CareerRecommendationResponse(BaseModel):
    id: int
    recommendation_type: str
    title: str
    description: Optional[str]
    priority: str
    reason: Optional[str]
    is_dismissed: bool
    is_completed: bool
    created_at: datetime

    class Config:
        from_attributes = True


class SkillAnalyticsResponse(BaseModel):
    id: int
    skill_name: str
    category: Optional[str]
    proficiency_level: float
    source: Optional[str]
    evidence_count: int
    trend: str
    last_assessed: Optional[datetime]

    class Config:
        from_attributes = True


class PerformanceMetricsResponse(BaseModel):
    id: int
    metric_type: str
    session_id: Optional[int]
    overall_score: Optional[float]
    topic_scores: Optional[str]
    weak_topics: Optional[str]
    strong_topics: Optional[str]
    difficulty_level: Optional[str]
    role: Optional[str]
    completed_at: Optional[datetime]
    created_at: datetime

    class Config:
        from_attributes = True


class SkillHeatmapResponse(BaseModel):
    skills: List[SkillAnalyticsResponse]
    categories: dict
    overall_proficiency: float
