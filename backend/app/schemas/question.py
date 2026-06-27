from pydantic import BaseModel
from typing import Optional

class QuestionResponse(BaseModel):
    id: int
    question_text: str
    answer_text: Optional[str] = None
    topic: Optional[str] = None
    difficulty: Optional[str] = None
    score: Optional[int] = None
    score_accuracy: Optional[int] = None
    score_communication: Optional[int] = None
    score_confidence: Optional[int] = None
    score_completeness: Optional[int] = None
    feedback: Optional[str] = None
    improvement_tips: Optional[str] = None

    class Config:
        from_attributes = True
