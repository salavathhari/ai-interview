from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime

class JobRoleCreate(BaseModel):
    title: str
    description: str
    requirements: str

class JobRoleResponse(BaseModel):
    id: int
    title: str
    description: str
    requirements: str
    invite_code: Optional[str] = None
    created_at: datetime
    is_active: bool

    class Config:
        from_attributes = True

class CandidateSummary(BaseModel):
    user_email: str
    user_name: str
    score: Optional[float]
    status: str
    started_at: datetime
    session_id: int
    rank: Optional[int] = None

class RecruiterDashboard(BaseModel):
    active_jobs: int
    total_applicants: int
    avg_candidate_score: float
    recent_candidates: List[CandidateSummary]
    strongest_skills: List[str] = []
    hiring_recommendations: List[str] = []
