from sqlalchemy import Column, Integer, String, Text, ForeignKey, DateTime
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.database import Base

class Question(Base):
    __tablename__ = "questions"

    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(Integer, ForeignKey("interview_sessions.id"))
    question_text = Column(Text)
    topic = Column(String, nullable=True)
    difficulty = Column(String, nullable=True)
    answer_text = Column(Text, nullable=True)
    feedback = Column(Text, nullable=True)
    improvement_tips = Column(Text, nullable=True)

    score = Column(Integer, nullable=True)
    # Step 13: Detailed Analytics Metrics
    score_accuracy = Column(Integer, nullable=True)
    score_communication = Column(Integer, nullable=True)
    score_confidence = Column(Integer, nullable=True)
    score_completeness = Column(Integer, nullable=True)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    session = relationship("InterviewSession", back_populates="questions")
    metrics = relationship("InterviewQuestionMetric", back_populates="question")
