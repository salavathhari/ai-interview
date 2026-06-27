from pydantic import BaseModel
from typing import List, Optional, Dict, Any
from datetime import datetime


# ─── Test Cases ───────────────────────────────────────────────────────────────

class TestCase(BaseModel):
    input: str
    expected: str


class TestCaseResult(BaseModel):
    """Per-test-case execution result (returned to frontend)"""
    test_number: int
    passed: bool
    runtime_ms: Optional[int] = None
    memory_kb: Optional[int] = None
    # For public test cases only — never expose hidden TC inputs
    input: Optional[str] = None
    expected: Optional[str] = None
    actual: Optional[str] = None
    error: Optional[str] = None


# ─── Challenge ────────────────────────────────────────────────────────────────

class ExampleCase(BaseModel):
    input: str
    output: str
    explanation: Optional[str] = None


class CodingChallengeBase(BaseModel):
    title: str
    description: str
    difficulty: str


class CodingChallengeResponse(CodingChallengeBase):
    id: int
    supported_languages: Optional[List[str]] = ["python"]
    starter_codes: Optional[Dict[str, str]] = {}
    topics: Optional[List[str]] = []
    role_tags: Optional[List[str]] = []
    constraints: Optional[str] = None
    examples: Optional[List[Dict[str, Any]]] = []
    # Public test cases only (no hidden)
    test_cases: Optional[List[Dict[str, str]]] = []
    time_limit_ms: Optional[int] = 5000
    memory_limit_kb: Optional[int] = 131072

    class Config:
        from_attributes = True


# ─── Coding Session ───────────────────────────────────────────────────────────

class CodingSessionCreate(BaseModel):
    interview_session_id: Optional[int] = None
    language: Optional[str] = "python"


class CodingSessionResponse(BaseModel):
    id: int
    user_id: int
    interview_session_id: Optional[int] = None
    challenge_id: Optional[int] = None
    language_used: str
    status: str
    coding_score: Optional[float] = None
    started_at: datetime
    ended_at: Optional[datetime] = None
    challenge: Optional[CodingChallengeResponse] = None

    class Config:
        from_attributes = True


# ─── Code Execution ───────────────────────────────────────────────────────────

class CodingRunCreate(BaseModel):
    coding_session_id: Optional[int] = None
    challenge_id: int
    code: str
    language: str


class CodingRunResponse(BaseModel):
    status: str
    runtime_ms: Optional[int] = None
    memory_kb: Optional[int] = None
    output: Optional[str] = None
    all_passed: bool = False
    public_results: List[TestCaseResult] = []
    # Hidden: only count, never inputs
    hidden_total: int = 0
    hidden_passed: int = 0


# ─── Submission ───────────────────────────────────────────────────────────────

class CodingSubmissionCreate(BaseModel):
    coding_session_id: Optional[int] = None
    challenge_id: int
    session_id: Optional[int] = None  # legacy
    code: str
    language: str


class AIReview(BaseModel):
    score: float
    feedback: str
    time_complexity: Optional[str] = None
    space_complexity: Optional[str] = None
    strengths: List[str] = []
    suggestions: List[str] = []


class CodingSubmissionResponse(BaseModel):
    id: int
    status: str
    language: Optional[str] = "python"
    runtime_ms: Optional[int] = None
    memory_kb: Optional[int] = None
    output: Optional[str] = None
    correctness_score: Optional[float] = None
    ai_feedback: Optional[str] = None
    ai_score: Optional[float] = None
    time_complexity: Optional[str] = None
    space_complexity: Optional[str] = None
    is_final: bool = False
    test_results: Optional[List[TestCaseResult]] = None
    created_at: datetime

    class Config:
        from_attributes = True


class SubmissionHistoryItem(BaseModel):
    id: int
    status: str
    language: Optional[str] = None
    runtime_ms: Optional[int] = None
    memory_kb: Optional[int] = None
    correctness_score: Optional[float] = None
    ai_score: Optional[float] = None
    is_final: bool = False
    created_at: datetime

    class Config:
        from_attributes = True


class SubmissionHistoryResponse(BaseModel):
    submissions: List[SubmissionHistoryItem]
    total: int
