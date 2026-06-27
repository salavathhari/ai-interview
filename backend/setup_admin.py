from sqlalchemy import text
from app.database import engine
from app.auth.utils import get_password_hash

def setup_admin():
    with engine.connect() as conn:
        print("Ensuring columns exist...")
        try:
            conn.execute(text('ALTER TABLE users ADD COLUMN is_admin BOOLEAN DEFAULT FALSE;'))
            conn.commit()
        except Exception:
            print("is_admin column already exists.")

        # Create a default admin user for testing
        password_hash = get_password_hash('admin123')
        try:
            conn.execute(
                text("INSERT INTO users (email, name, hashed_password, is_admin, is_active) VALUES (:email, :name, :pw, :admin, :active)"),
                {"email": "admin@ai-platform.com", "name": "System Admin", "pw": password_hash, "admin": True, "active": True}
            )
            conn.commit()
            print("Admin user created: admin@ai-platform.com / admin123")
        except Exception as e:
            print(f"Note: Admin user might already exist or row skipped.")

if __name__ == "__main__":
    setup_admin()
