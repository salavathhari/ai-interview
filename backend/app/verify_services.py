import os
import sys

# Add backend to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.database import engine, Base, SessionLocal, init_models
from app.services.ai_service import AIService
from app.services.report_service import ReportService

def verify():
    print("--- 1. Verification: Database Schema ---")
    init_models()
    Base.metadata.create_all(bind=engine)
    print("Database tables ensured.")

    print("\n--- 2. Verification: AI Service (Mock Mode) ---")
    mock_q = "What is the difference between shallow copy and deep copy in Python?"
    mock_a = "Shallow copy only copies the reference, deep copy copies the whole object recursively."
    
    eval_result = AIService.evaluate_answer(mock_q, mock_a)
    print(f"Evaluation Test Output: {eval_result}")
    
    if isinstance(eval_result, dict) and "score" in eval_result:
        print("✅ AI Evaluation format correct.")
    else:
        print("❌ AI Evaluation format incorrect.")

    print("\n--- 3. Verification: Adaptive Logic ---")
    easy_q = AIService.get_difficulty_adjustment("Medium", score=2)
    hard_q = AIService.get_difficulty_adjustment("Medium", score=9)
    print(f"Difficulty Change (Lower): Medium + Score 2 -> {easy_q}")
    print(f"Difficulty Change (Higher): Medium + Score 9 -> {hard_q}")
    
    if easy_q == "Easy" and hard_q == "Hard":
        print("✅ Adaptive logic working.")
    else:
        print("❌ Adaptive logic mismatch.")

    print("\n--- 4. Verification: Report Service ---")
    db = SessionLocal()
    from app.models.user import User
    from app.models.interview_session import InterviewSession
    from app.models.question import Question
    try:
        # Create a dummy user/session for report test
        user = db.query(User).first()
        if not user:
            user = User(email="test@verify.com", name="Test Verify", hashed_password="pw")
            db.add(user)
            db.commit()
            db.refresh(user)
        
        session = InterviewSession(user_id=user.id, role="Backend Developer", status="completed", score=8.5)
        db.add(session)
        db.commit()
        db.refresh(session)
        
        q1 = Question(session_id=session.id, question_text=mock_q, answer_text=mock_a, score=9, topic="Python")
        db.add(q1)
        db.commit()
        
        summary = ReportService.generate_ai_summary(session, [q1])
        print(f"Summary Generated: {summary.get('summary', 'FAILED')[:100]}...")
        
        if "summary" in summary and "roadmap" in summary:
            print("✅ Report generation logic verified.")
        else:
            print("❌ Report generation logic failed.")
            
    except Exception as e:
        print(f"Error in Report Verification: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    verify()
