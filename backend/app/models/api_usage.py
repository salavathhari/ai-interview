from sqlalchemy import Column, Integer, String, DateTime, Float
from sqlalchemy.sql import func
from app.database import Base

class ApiUsage(Base) :
    __tablename__ = "api_usage"

    id = Column(Integer, primary_key=True, index=True)
    provider = Column(String, default="openai")
    model = Column(String)
    feature = Column(String)  # e.g., "interview-evaluation", "resume-parsing"
    prompt_tokens = Column(Integer)
    completion_tokens = Column(Integer)
    total_tokens = Column(Integer)
    cost = Column(Float)  # Estimated cost in USD
    timestamp = Column(DateTime(timezone=True), server_default=func.now())
