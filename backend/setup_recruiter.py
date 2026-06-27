from sqlalchemy import text
from app.database import engine
from app.auth.utils import get_password_hash

def setup_recruiter():
    # Use individual connections for each statement to avoid transaction aborts
    def run_sql(sql):
        with engine.connect() as conn:
            try:
                conn.execute(text(sql))
                conn.commit()
                print(f"Success: {sql[:50]}...")
            except Exception as e:
                print(f"Skipped/Error on: {sql[:50]}... -> {str(e)[:100]}")

    print("Ensuring columns exist for recruiter mode...")
    run_sql('ALTER TABLE users ADD COLUMN is_recruiter BOOLEAN DEFAULT FALSE;')
    run_sql('ALTER TABLE interview_sessions ADD COLUMN job_role_id INTEGER REFERENCES job_roles(id);')

    # Create a default recruiter user for testing
    password_hash = get_password_hash('recruiter123')
    with engine.connect() as conn:
        try:
            conn.execute(
                text("INSERT INTO users (email, name, hashed_password, is_recruiter, is_active) VALUES (:email, :name, :pw, :rec, :active)"),
                {"email": "recruiter@hiring.com", "name": "Global Recruiter", "pw": password_hash, "rec": True, "active": True}
            )
            conn.commit()
            print("Recruiter user created: recruiter@hiring.com / recruiter123")
        except Exception:
            print("Note: Recruiter user already exists.")

if __name__ == "__main__":
    setup_recruiter()
