from sqlalchemy import Column, Integer, String, Text, Boolean, ForeignKey, DateTime
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.database import Base


class Resume(Base):
    __tablename__ = "resumes"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), index=True)
    filename = Column(String)
    file_path = Column(String)
    extracted_text = Column(Text)
    skills = Column(String, nullable=True)
    content_hash = Column(String(32), nullable=True, index=True)
    version = Column(Integer, default=1)
    is_active = Column(Boolean, default=False, index=True)
    parsed_name = Column(String, nullable=True)
    parsed_email = Column(String, nullable=True)
    parsed_phone = Column(String, nullable=True)
    parsed_location = Column(String, nullable=True)
    parsed_linkedin = Column(String, nullable=True)
    parsed_github = Column(String, nullable=True)
    parsed_portfolio = Column(String, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    user = relationship("User", back_populates="resumes")
    versions = relationship("ResumeVersion", back_populates="resume", cascade="all, delete-orphan")


class ResumeVersion(Base):
    __tablename__ = "resume_versions"

    id = Column(Integer, primary_key=True, index=True)
    resume_id = Column(Integer, ForeignKey("resumes.id", ondelete="CASCADE"), index=True)
    user_id = Column(Integer, ForeignKey("users.id"), index=True)
    version_number = Column(Integer, nullable=False)
    filename = Column(String)
    file_path = Column(String)
    extracted_text = Column(Text)
    skills = Column(String, nullable=True)
    content_hash = Column(String(32), nullable=True)
    change_reason = Column(String(255), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    resume = relationship("Resume", back_populates="versions")
