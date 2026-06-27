from pydantic import BaseModel, ConfigDict
from typing import Optional, List
from datetime import datetime
from app.schemas.question import QuestionResponse

class InterviewSessionBase(BaseModel):
    role: str

class InterviewSessionCreate(InterviewSessionBase):
    invite_code: Optional[str] = None
    difficulty: Optional[str] = "Medium"
    interview_type: Optional[str] = "Technical"
    job_description_id: Optional[int] = None

class InterviewSessionResponse(InterviewSessionBase):
    id: int
    user_id: int
    status: str
    score: Optional[float] = None
    difficulty: str
    interview_type: str
    job_description_id: Optional[int] = None

    score_dsa: Optional[float] = None
    score_dbms: Optional[float] = None
    score_os: Optional[float] = None
    score_cn: Optional[float] = None
    score_oop: Optional[float] = None
    score_system_design: Optional[float] = None
    score_project: Optional[float] = None
    score_hr: Optional[float] = None
    score_communication: Optional[float] = None

    started_at: datetime
    ended_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)

class InterviewSessionDetailed(InterviewSessionResponse):
    questions: List[QuestionResponse]
