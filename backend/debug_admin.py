from app.database import SessionLocal
from app.models.user import User
from app.models.interview_session import InterviewSession
from app.models.resume import Resume
from app.models.question import Question
from app.models.interview_question_metric import InterviewQuestionMetric
from app.models.coding_challenge import CodingChallenge, CodingSubmission
from app.models.cheating_log import CheatingLog
from app.models.job_role import JobRole
from app.models.api_usage import ApiUsage

def ensure_admin(email):
    db = SessionLocal()
    user = db.query(User).filter(User.email == email).first()
    if user:
        user.is_admin = True
        db.commit()
        print(f"User {email} is now an admin.")
    else:
        print(f"User {email} not found.")
    db.close()

if __name__ == "__main__":
    ensure_admin("admin@ai-platform.com")
