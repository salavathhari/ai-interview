from pydantic import BaseModel
from typing import List, Dict, Any, Optional
from datetime import datetime


# ─── Existing schemas (preserved) ────────────────────────────────────────────

class UserStatus(BaseModel):
    id: int
    email: str
    name: str
    is_active: bool
    is_admin: bool
    session_count: int
    created_at: datetime


class AdminStatsResponse(BaseModel):
    total_users: int
    total_interviews: int
    total_questions_asked: int
    avg_score_platform: float
    interviews_by_role: Dict[str, int]
    recent_activity: List[Dict[str, Any]]
    total_api_cost: float


class CheatingLogResponse(BaseModel):
    id: int
    session_id: int
    event_type: str
    details: Any
    created_at: datetime
    user_email: Optional[str] = None

    class Config:
        from_attributes = True


class ApiUsageStats(BaseModel):
    total_tokens: int
    total_cost: float
    usage_by_feature: Dict[str, int]


# ─── Admin Dashboard ──────────────────────────────────────────────────────────

class AdminDashboardStats(BaseModel):
    total_users: int
    active_users: int
    total_interviews: int
    interviews_today: int
    total_recruiters: int
    total_reports: int
    active_voice_sessions: int
    api_requests_today: int
    avg_score_platform: float
    total_api_cost: float
    interviews_by_role: Dict[str, int]
    recent_activity: List[Dict[str, Any]]


# ─── Users ────────────────────────────────────────────────────────────────────

class UserDetail(BaseModel):
    id: int
    name: str
    email: str
    is_active: bool
    is_admin: bool
    is_recruiter: bool
    total_interviews: int
    avg_score: Optional[float]
    created_at: datetime

    class Config:
        from_attributes = True


class UserListResponse(BaseModel):
    users: List[UserDetail]
    total: int
    page: int
    per_page: int


class PasswordResetResponse(BaseModel):
    temp_password: str
    message: str


# ─── Recruiters ───────────────────────────────────────────────────────────────

class RecruiterDetail(BaseModel):
    id: int
    name: str
    email: str
    is_active: bool
    total_jobs: int
    total_candidates: int
    interviews_conducted: int
    created_at: datetime

    class Config:
        from_attributes = True


class RecruiterListResponse(BaseModel):
    recruiters: List[RecruiterDetail]
    total: int


# ─── Interviews ───────────────────────────────────────────────────────────────

class InterviewDetail(BaseModel):
    id: int
    candidate_name: str
    candidate_email: str
    role: str
    interview_type: str
    difficulty: str
    status: str
    score: Optional[float]
    started_at: datetime
    ended_at: Optional[datetime]
    duration_minutes: Optional[float]

    class Config:
        from_attributes = True


class InterviewListResponse(BaseModel):
    interviews: List[InterviewDetail]
    total: int
    page: int
    per_page: int


# ─── Voice Sessions ───────────────────────────────────────────────────────────

class VoiceSessionSummary(BaseModel):
    id: int
    candidate_name: str
    candidate_email: str
    status: str
    score: Optional[float]
    started_at: datetime
    ended_at: Optional[datetime]
    duration_minutes: Optional[float]

    class Config:
        from_attributes = True


# ─── AI Usage ────────────────────────────────────────────────────────────────

class AIUsageDailyPoint(BaseModel):
    date: str
    requests: int
    tokens: int
    cost: float


class AIUsageDetail(BaseModel):
    total_requests: int
    total_tokens: int
    total_cost: float
    avg_response_time_ms: float
    failed_requests: int
    usage_by_feature: Dict[str, Any]
    daily_breakdown: List[AIUsageDailyPoint]


# ─── Reports ─────────────────────────────────────────────────────────────────

class ReportItem(BaseModel):
    id: int
    candidate_name: str
    candidate_email: str
    role: str
    score: Optional[float]
    interview_type: str
    status: str
    generated_at: datetime

    class Config:
        from_attributes = True


class ReportListResponse(BaseModel):
    reports: List[ReportItem]
    total: int


# ─── Platform Analytics ───────────────────────────────────────────────────────

class GrowthPoint(BaseModel):
    date: str
    count: int


class ScoreDistributionBucket(BaseModel):
    range: str
    count: int


class PlatformAnalytics(BaseModel):
    total_users: int
    active_users: int
    new_signups_this_month: int
    interview_completion_rate: float
    avg_interview_score: float
    most_popular_role: str
    most_popular_interview_type: str
    user_growth: List[GrowthPoint]
    interview_trends: List[GrowthPoint]
    score_distribution: List[ScoreDistributionBucket]


# ─── System Health ────────────────────────────────────────────────────────────

class ServiceHealth(BaseModel):
    name: str
    status: str          # "online", "offline", "warning"
    latency_ms: Optional[float]
    details: Optional[str]


class SystemHealthStatus(BaseModel):
    overall: str
    services: List[ServiceHealth]
    error_rate: float
    active_connections: int
    checked_at: datetime


# ─── Audit Logs ───────────────────────────────────────────────────────────────

class AuditLogEntry(BaseModel):
    id: int
    action: str
    admin_email: Optional[str]
    target_type: Optional[str]
    target_id: Optional[int]
    details: Optional[Any]
    timestamp: datetime

    class Config:
        from_attributes = True


class AuditLogListResponse(BaseModel):
    logs: List[AuditLogEntry]
    total: int
    page: int
    per_page: int


# ─── Notifications ────────────────────────────────────────────────────────────

class NotificationItem(BaseModel):
    id: int
    title: str
    message: str
    type: str
    is_read: bool
    created_at: datetime

    class Config:
        from_attributes = True


# ─── Settings ────────────────────────────────────────────────────────────────

class AdminSettings(BaseModel):
    platform_name: str
    max_interviews_per_user: int
    max_tokens_per_interview: int
    ai_model: str
    voice_enabled: bool
    maintenance_mode: bool


# ─── Coding Admin ────────────────────────────────────────────────────────────

class AdminCodingSubmission(BaseModel):
    id: int
    candidate_email: str
    challenge_title: str
    language: str
    status: str
    correctness_score: Optional[float] = None
    ai_score: Optional[float] = None
    runtime_ms: Optional[int] = None
    memory_kb: Optional[int] = None
    is_final: bool
    created_at: datetime

    class Config:
        from_attributes = True


class AdminCodingSubmissionsResponse(BaseModel):
    submissions: List[AdminCodingSubmission]
    total_pages: int
    total: int
    page: int
    per_page: int


class AdminCodingAnalytics(BaseModel):
    total_submissions: int
    total_sessions: int
    avg_correctness_score: float
    avg_ai_score: float
    language_distribution: Dict[str, int]
    status_distribution: Dict[str, int]
    difficulty_breakdown: Dict[str, int]


class AdminCodingSubmissionDetail(BaseModel):
    id: int
    candidate_email: str
    challenge_title: str
    language: str
    status: str
    correctness_score: Optional[float] = None
    ai_score: Optional[float] = None
    runtime_ms: Optional[int] = None
    memory_kb: Optional[int] = None
    is_final: bool
    created_at: datetime
    code: str
    ai_feedback: Optional[str] = None
    time_complexity: Optional[str] = None
    space_complexity: Optional[str] = None
    test_results: Optional[List[Any]] = None
    hidden_passed: int
    hidden_total: int

    class Config:
        from_attributes = True

