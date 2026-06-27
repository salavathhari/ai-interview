from sqlalchemy import Column, Integer, String, Text, Float, Boolean, DateTime, ForeignKey
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.database import Base


class GeneratedReport(Base):
    """Stores generated career portfolio reports for persistent access."""
    __tablename__ = "generated_reports"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), index=True)
    title = Column(String, nullable=False)
    report_type = Column(String, nullable=False)  # portfolio/interview/coding/ats/skill-gap/career-readiness
    status = Column(String, default="ready")  # ready/outdated/generating/failed
    file_path = Column(String, nullable=True)  # path to generated PDF
    file_size = Column(Integer, nullable=True)  # file size in bytes
    summary = Column(Text, nullable=True)  # AI-generated executive summary
    scores_snapshot = Column(Text, nullable=True)  # JSON: snapshot of all scores at generation time
    is_outdated = Column(Boolean, default=False)  # True when underlying data has changed
    outdated_reason = Column(String, nullable=True)  # What changed to make this report outdated
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    user = relationship("User")
