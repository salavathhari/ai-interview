"""
Migration script: Add new columns to interview_sessions table.
Run once from the backend directory:
    python migrate_interview_columns.py
"""
import sqlite3
import os

DB_PATH = os.getenv("DATABASE_URL", "sqlite:///./sql_app_v2.db").replace("sqlite:///", "").replace("./", "")

COLUMNS_TO_ADD = [
    ("difficulty",       "TEXT DEFAULT 'Medium'"),
    ("interview_type",   "TEXT DEFAULT 'Technical'"),
    ("score_dsa",        "REAL"),
    ("score_dbms",       "REAL"),
    ("score_os",         "REAL"),
    ("score_cn",         "REAL"),
    ("score_oop",        "REAL"),
    ("score_system_design", "REAL"),
    ("score_project",    "REAL"),
    ("score_hr",         "REAL"),
    ("score_communication", "REAL"),
]

def migrate():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # Fetch existing columns
    cursor.execute("PRAGMA table_info(interview_sessions)")
    existing = {row[1] for row in cursor.fetchall()}

    added = []
    skipped = []
    for col_name, col_def in COLUMNS_TO_ADD:
        if col_name in existing:
            skipped.append(col_name)
        else:
            cursor.execute(f"ALTER TABLE interview_sessions ADD COLUMN {col_name} {col_def}")
            added.append(col_name)

    conn.commit()
    conn.close()

    print(f"Migration complete.")
    print(f"  Added   : {added if added else 'none'}")
    print(f"  Skipped : {skipped if skipped else 'none (already existed)'}")

if __name__ == "__main__":
    migrate()
