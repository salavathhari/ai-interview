import os
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

SQLALCHEMY_DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./sql_app_v2.db")

# For SQLite, we need 'check_same_thread': False
connect_args = {"check_same_thread": False} if SQLALCHEMY_DATABASE_URL.startswith("sqlite") else {}

engine = create_engine(
    SQLALCHEMY_DATABASE_URL, connect_args=connect_args
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

# Import all models to ensure they are registered with Base.metadata
def init_models():
    from app.models.user import User
    from app.models.resume import Resume, ResumeVersion
    from app.models.interview_session import InterviewSession
    from app.models.question import Question
    from app.models.interview_question_metric import InterviewQuestionMetric
    from app.models.coding_challenge import CodingChallenge, CodingSubmission, CodingSession
    from app.models.cheating_log import CheatingLog
    from app.models.job_role import JobRole
    from app.models.api_usage import ApiUsage
    from app.models.career import JobDescription, ResumeAnalysis, SkillGapAnalysis, LearningRoadmap, OptimizedResume, CareerReadiness, CareerReadinessHistory
    from app.models.intelligence import SkillDependency, LearningProgress, CareerRecommendation, PerformanceMetrics, SkillAnalytics
    from app.models.ats_report import ATSReport
    from app.models.token_blacklist import TokenBlacklist
    from app.models.ml_analytics import (
        MLClassification, MLATSPrediction, MLSkillExtraction,
        MLJobRecommendation, MLResumeEmbedding, MLSearchLog,
        MLQualityPrediction, MLAnalysisHistory,
    )
    from app.models.analytics import AnalyticsEvent, AnalyticsSummary
    from app.models.generated_report import GeneratedReport

    # SQLite migrations for nullable columns not handled by create_all
    _run_sqlite_migrations()


def _run_sqlite_migrations():
    """Run SQLite-specific column migrations that create_all() doesn't handle."""
    import sqlite3
    db_url = str(engine.url)
    if not db_url.startswith("sqlite"):
        return

    try:
        conn = engine.raw_connection()
        cursor = conn.cursor()

        # Migrate interview_sessions
        cursor.execute("PRAGMA table_info(interview_sessions)")
        columns = {row[1] for row in cursor.fetchall()}
        if "job_description_id" not in columns:
            try:
                cursor.execute("ALTER TABLE interview_sessions ADD COLUMN job_description_id INTEGER REFERENCES job_descriptions(id)")
            except Exception:
                pass

        # Migrate career_readiness
        cursor.execute("PRAGMA table_info(career_readiness)")
        columns = {row[1] for row in cursor.fetchall()}
        for col_name, col_type in [
            ("project_score", "REAL"), ("consistency_score", "REAL"),
            ("learning_score", "REAL"), ("role_match_score", "REAL"),
            ("company_match_score", "REAL"), ("score_breakdown", "TEXT"),
            ("target_role", "TEXT"), ("target_company", "TEXT"), ("updated_at", "DATETIME"),
        ]:
            if col_name not in columns:
                try:
                    cursor.execute(f"ALTER TABLE career_readiness ADD COLUMN {col_name} {col_type}")
                except Exception:
                    pass

        # Migrate career_readiness_history
        cursor.execute("PRAGMA table_info(career_readiness_history)")
        columns = {row[1] for row in cursor.fetchall()}
        for col_name, col_type in [
            ("trigger_event", "TEXT"), ("learning_score", "REAL"),
        ]:
            if col_name not in columns:
                try:
                    cursor.execute(f"ALTER TABLE career_readiness_history ADD COLUMN {col_name} {col_type}")
                except Exception:
                    pass

        # Migrate learning_roadmaps
        cursor.execute("PRAGMA table_info(learning_roadmaps)")
        columns = {row[1] for row in cursor.fetchall()}
        for col_name, col_type in [
            ("phases", "TEXT"), ("current_phase_index", "INTEGER"),
            ("daily_plan", "TEXT"), ("mentor_tips", "TEXT"),
            ("skill_gap_summary", "TEXT"), ("career_goal", "TEXT"),
            ("target_role", "TEXT"), ("target_company", "TEXT"),
            ("current_readiness", "REAL"), ("target_readiness", "REAL"),
            ("interview_readiness", "REAL"), ("coding_readiness", "REAL"),
            ("version", "INTEGER"), ("updated_at", "DATETIME"),
        ]:
            if col_name not in columns:
                try:
                    cursor.execute(f"ALTER TABLE learning_roadmaps ADD COLUMN {col_name} {col_type}")
                except Exception:
                    pass

        conn.commit()
        conn.close()
    except Exception:
        pass

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
