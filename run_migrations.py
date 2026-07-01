"""Run PostgreSQL migrations for new recruiter integration tables and columns."""
import sys
sys.path.insert(0, 'backend')

from app.database import engine
from sqlalchemy import text

def run_migrations():
    conn = engine.connect()
    
    # 1. Create companies table
    conn.execute(text("""
        CREATE TABLE IF NOT EXISTS companies (
            id SERIAL PRIMARY KEY,
            name VARCHAR(200) NOT NULL,
            description TEXT,
            website VARCHAR(500),
            logo_url VARCHAR(500),
            industry VARCHAR(100),
            size VARCHAR(50),
            location VARCHAR(200),
            recruiter_id INTEGER REFERENCES users(id),
            is_active BOOLEAN DEFAULT TRUE,
            created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
            updated_at TIMESTAMP WITH TIME ZONE
        )
    """))
    print("OK: companies table")

    # 2. Create application_notes table
    conn.execute(text("""
        CREATE TABLE IF NOT EXISTS application_notes (
            id SERIAL PRIMARY KEY,
            application_id INTEGER REFERENCES applications(id),
            recruiter_id INTEGER REFERENCES users(id),
            note TEXT NOT NULL,
            is_internal BOOLEAN DEFAULT TRUE,
            created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
            updated_at TIMESTAMP WITH TIME ZONE
        )
    """))
    print("OK: application_notes table")

    # 3. Create candidate_assignments table
    conn.execute(text("""
        CREATE TABLE IF NOT EXISTS candidate_assignments (
            id SERIAL PRIMARY KEY,
            application_id INTEGER REFERENCES applications(id),
            assignment_type VARCHAR(20),
            template_id INTEGER,
            assigned_by INTEGER REFERENCES users(id),
            assigned_to INTEGER REFERENCES users(id),
            status VARCHAR(20) DEFAULT 'pending',
            due_date TIMESTAMP WITH TIME ZONE,
            notes TEXT,
            created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
            completed_at TIMESTAMP WITH TIME ZONE
        )
    """))
    print("OK: candidate_assignments table")

    # 4. Add new columns to recruiter_job_posts
    new_job_cols = [
        ("company_id", "INTEGER REFERENCES companies(id)"),
        ("title", "VARCHAR(300)"),
        ("description", "TEXT"),
    ]
    for col, col_type in new_job_cols:
        try:
            conn.execute(text(f"ALTER TABLE recruiter_job_posts ADD COLUMN {col} {col_type}"))
            print(f"OK: recruiter_job_posts.{col}")
        except Exception as e:
            print(f"SKIP: recruiter_job_posts.{col} ({e})")

    # 5. Add new columns to applications
    new_app_cols = [
        ("recruiter_id", "INTEGER REFERENCES users(id)"),
        ("resume_analysis_id", "INTEGER REFERENCES resume_analyses(id)"),
        ("ats_score", "REAL"),
        ("resume_match_score", "REAL"),
        ("skill_gap_score", "REAL"),
        ("career_readiness_score", "REAL"),
        ("screening_summary", "TEXT"),
        ("matched_skills", "TEXT"),
        ("missing_skills", "TEXT"),
        ("experience_match", "REAL"),
        ("education_match", "REAL"),
        ("interview_session_id", "INTEGER REFERENCES interview_sessions(id)"),
        ("coding_session_id", "INTEGER REFERENCES coding_sessions(id)"),
        ("final_interview_score", "REAL"),
        ("final_coding_score", "REAL"),
        ("final_composite_score", "REAL"),
        ("hiring_recommendation", "TEXT"),
        ("strengths", "TEXT"),
        ("weaknesses", "TEXT"),
        ("decision", "TEXT"),
        ("decision_at", "TIMESTAMP WITH TIME ZONE"),
        ("decision_by", "INTEGER REFERENCES users(id)"),
        ("decision_reason", "TEXT"),
        ("screened_at", "TIMESTAMP WITH TIME ZONE"),
    ]
    for col, col_type in new_app_cols:
        try:
            conn.execute(text(f"ALTER TABLE applications ADD COLUMN {col} {col_type}"))
            print(f"OK: applications.{col}")
        except Exception as e:
            print(f"SKIP: applications.{col} ({e})")

    # 6. Add new columns to application_history
    new_hist_cols = [
        ("actor_id", "INTEGER REFERENCES users(id)"),
        ("actor_role", "TEXT"),
    ]
    for col, col_type in new_hist_cols:
        try:
            conn.execute(text(f"ALTER TABLE application_history ADD COLUMN {col} {col_type}"))
            print(f"OK: application_history.{col}")
        except Exception as e:
            print(f"SKIP: application_history.{col} ({e})")

    conn.commit()
    conn.close()
    print("\nAll migrations complete!")

if __name__ == "__main__":
    run_migrations()
