import logging
import os
import re
from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, sessionmaker
from dotenv import load_dotenv

load_dotenv(os.path.join(os.path.dirname(os.path.dirname(__file__)), ".env"))

SQLALCHEMY_DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./sql_app_v2.db")

is_sqlite = SQLALCHEMY_DATABASE_URL.startswith("sqlite")

if is_sqlite:
    connect_args = {"check_same_thread": False}
    engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args=connect_args)
else:
    engine = create_engine(
        SQLALCHEMY_DATABASE_URL,
        pool_size=5,
        max_overflow=10,
        pool_pre_ping=True,
        pool_recycle=300,
    )

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# #18: Use modern DeclarativeBase instead of deprecated declarative_base()
class Base(DeclarativeBase):
    pass

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
    from app.models.admin_log import AdminLog
    from app.models.system_health_log import SystemHealthLog
    from app.models.notification import Notification
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


_SQLITE_MIGRATIONS = {
    "interview_sessions": [
        ("job_description_id", "INTEGER REFERENCES job_descriptions(id)"),
    ],
    "career_readiness": [
        ("project_score", "REAL"), ("consistency_score", "REAL"),
        ("learning_score", "REAL"), ("role_match_score", "REAL"),
        ("company_match_score", "REAL"), ("score_breakdown", "TEXT"),
        ("target_role", "TEXT"), ("target_company", "TEXT"), ("updated_at", "DATETIME"),
    ],
    "career_readiness_history": [
        ("trigger_event", "TEXT"), ("learning_score", "REAL"),
    ],
    "learning_roadmaps": [
        ("phases", "TEXT"), ("current_phase_index", "INTEGER"),
        ("daily_plan", "TEXT"), ("mentor_tips", "TEXT"),
        ("skill_gap_summary", "TEXT"), ("career_goal", "TEXT"),
        ("target_role", "TEXT"), ("target_company", "TEXT"),
        ("current_readiness", "REAL"), ("target_readiness", "REAL"),
        ("interview_readiness", "REAL"), ("coding_readiness", "REAL"),
        ("version", "INTEGER"), ("updated_at", "DATETIME"),
    ],
}

_VALID_IDENTIFIER_RE = re.compile(r"^[a-zA-Z_][a-zA-Z0-9_]*$")
_VALID_TYPE_RE = re.compile(r"^(INTEGER|REAL|TEXT|DATETIME|BOOLEAN)$")


def _validate_identifier(name: str) -> bool:
    return bool(_VALID_IDENTIFIER_RE.match(name))


def _validate_column_type(col_type: str) -> bool:
    return bool(_VALID_TYPE_RE.match(col_type))


def _run_sqlite_migrations():
    """Run SQLite-specific column migrations that create_all() doesn't handle."""
    db_url = str(engine.url)
    if not db_url.startswith("sqlite"):
        return

    try:
        conn = engine.raw_connection()
        cursor = conn.cursor()

        for table, migrations in _SQLITE_MIGRATIONS.items():
            cursor.execute(f"PRAGMA table_info({table})")
            columns = {row[1] for row in cursor.fetchall()}
            for col_name, col_type in migrations:
                if col_name in columns:
                    continue
                if not _validate_identifier(col_name) or not _validate_column_type(col_type):
                    logging.warning("Skipping invalid migration: %s.%s %s", table, col_name, col_type)
                    continue
                try:
                    cursor.execute(f"ALTER TABLE {table} ADD COLUMN {col_name} {col_type}")
                except Exception as e:
                    logging.debug("Migration skipped for %s.%s: %s", table, col_name, e)

        conn.commit()
        conn.close()
    except Exception as e:
        logging.error("SQLite migration failed: %s", e)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
