from pydantic import BaseModel
from datetime import datetime
from typing import Optional


class ResumeBase(BaseModel):
    filename: str
    extracted_text_snippet: str


class ResumeResponse(BaseModel):
    id: int
    filename: str
    extracted_text: str
    skills: Optional[str] = None
    content_hash: Optional[str] = None
    version: int = 1
    is_active: bool = False
    processing_status: str = "completed"  # pending, processing, completed, failed
    extraction_error: Optional[str] = None
    parsed_name: Optional[str] = None
    parsed_email: Optional[str] = None
    parsed_phone: Optional[str] = None
    parsed_location: Optional[str] = None
    parsed_linkedin: Optional[str] = None
    parsed_github: Optional[str] = None
    parsed_portfolio: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True
