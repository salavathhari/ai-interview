from sqlalchemy import Column, Integer, String, Text, ForeignKey, JSON, DateTime, Float, Boolean
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.database import Base
from app.models.user import User


class CodingChallenge(Base):
    __tablename__ = "coding_challenges"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, index=True)
    description = Column(Text)
    difficulty = Column(String)  # "Easy", "Medium", "Hard"

    # Multi-language support
    supported_languages = Column(JSON, default=["python", "java", "cpp", "javascript"])
    starter_codes = Column(JSON)  # {"python": "...", "java": "...", "cpp": "...", "javascript": "..."}

    # Problem metadata
    topics = Column(JSON, default=[])          # ["arrays", "hashmap"]
    role_tags = Column(JSON, default=[])       # ["SDE", "Backend", "Frontend"]
    constraints = Column(Text, nullable=True)  # Plain text constraints
    examples = Column(JSON, default=[])        # [{input, output, explanation}]

    # Test cases (split into public/hidden)
    test_cases = Column(JSON, default=[])        # Public: [{input, expected}]
    hidden_test_cases = Column(JSON, default=[]) # Hidden: [{input, expected}]

    # Execution limits
    time_limit_ms = Column(Integer, default=5000)
    memory_limit_kb = Column(Integer, default=131072)  # 128 MB

    # Legacy field kept for backwards compat
    language = Column(String, default="python")
    starter_code = Column(Text, nullable=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now())

    submissions = relationship("CodingSubmission", back_populates="challenge")
    coding_sessions = relationship("CodingSession", back_populates="challenge")


class CodingSubmission(Base):
    __tablename__ = "coding_submissions"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    challenge_id = Column(Integer, ForeignKey("coding_challenges.id"))
    session_id = Column(Integer, ForeignKey("interview_sessions.id"), nullable=True)
    coding_session_id = Column(Integer, ForeignKey("coding_sessions.id"), nullable=True)

    # Code submitted
    code = Column(Text)
    language = Column(String, default="python")

    # Execution results
    status = Column(String)  # "Accepted", "Wrong Answer", "Time Limit Exceeded", "Runtime Error", "Compilation Error"
    runtime_ms = Column(Integer, nullable=True)
    memory_kb = Column(Integer, nullable=True)
    output = Column(Text, nullable=True)

    # Detailed per-test results
    test_results = Column(JSON, nullable=True)  # [{input, expected, actual, passed, runtime_ms}]

    # Scoring
    correctness_score = Column(Float, nullable=True)  # % test cases passed (0-100)

    # AI Code Review
    ai_feedback = Column(Text, nullable=True)
    ai_score = Column(Float, nullable=True)       # 0-10 code quality
    time_complexity = Column(String, nullable=True)
    space_complexity = Column(String, nullable=True)

    # Distinguish run vs final submit
    is_final = Column(Boolean, default=False)

    created_at = Column(DateTime(timezone=True), server_default=func.now())

    challenge = relationship("CodingChallenge", back_populates="submissions")
    user = relationship("User")


class CodingSession(Base):
    """Tracks a candidate's entire coding round for one interview session."""
    __tablename__ = "coding_sessions"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    interview_session_id = Column(Integer, ForeignKey("interview_sessions.id"), nullable=True)
    challenge_id = Column(Integer, ForeignKey("coding_challenges.id"), nullable=True)

    language_used = Column(String, default="python")
    status = Column(String, default="in_progress")  # "in_progress", "submitted", "timed_out"
    coding_score = Column(Float, nullable=True)  # Combined correctness + AI quality score

    final_submission_id = Column(Integer, nullable=True)

    started_at = Column(DateTime(timezone=True), server_default=func.now())
    ended_at = Column(DateTime(timezone=True), nullable=True)

    user = relationship("User")
    challenge = relationship("CodingChallenge", back_populates="coding_sessions")
