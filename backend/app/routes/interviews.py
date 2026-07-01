from fastapi import APIRouter, Depends, HTTPException, status, Response, BackgroundTasks
from sqlalchemy.orm import Session
from typing import List
from app.database import get_db, SessionLocal
from app.auth.utils import get_current_user
from app.models.user import User
from app.models.interview_session import InterviewSession
from app.models.resume import Resume
from app.models.question import Question
from app.models.job_role import JobRole
from app.models.career import JobDescription
from app.schemas.interview_session import InterviewSessionCreate, InterviewSessionResponse, InterviewSessionDetailed
from app.services.ai_service import AIService
from app.services.report_service import ReportService

router = APIRouter(
    prefix="/interviews",
    tags=["interviews"]
)


# ─── Background Task Handlers ─────────────────────────────────────────────

def _generate_initial_question_bg(
    session_id: int,
    role: str,
    interview_type: str,
    difficulty: str,
    resume_text: str,
    job_description_id: int = None
):
    """Background task to generate first interview question asynchronously."""
    db = SessionLocal()
    try:
        # Get session and job description (if any)
        session = db.query(InterviewSession).filter(InterviewSession.id == session_id).first()
        if not session:
            return
        
        jd_text = ""
        if job_description_id:
            jd = db.query(JobDescription).filter(JobDescription.id == job_description_id).first()
            if jd:
                jd_text = jd.raw_text or ""
        
        # Generate question
        initial_q_data = AIService.generate_next_question(
            role=role,
            interview_type=interview_type,
            difficulty=difficulty,
            resume_text=resume_text,
            previous_questions=[],
            weak_topics=[],
            strong_topics=[],
            jd_text=jd_text
        )
        
        # Store question
        db_q = Question(
            session_id=session_id,
            question_text=initial_q_data["text"],
            topic=initial_q_data.get("topic"),
            difficulty=initial_q_data.get("difficulty")
        )
        db.add(db_q)
        
        # Mark session as ready
        session.status = "ready"
        db.commit()
        
    except Exception as e:
        print(f"Background question generation failed: {e}")
        # Update session status to error
        try:
            session = db.query(InterviewSession).filter(InterviewSession.id == session_id).first()
            if session:
                session.status = "error"
                db.commit()
        except:
            pass
    finally:
        db.close()


@router.post("/", response_model=InterviewSessionResponse)
def create_interview_session(
    session_in: InterviewSessionCreate,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    OPTIMIZED: Create interview session and return immediately.
    Initial question generation runs in background (reduces latency from 2-3s to <100ms).
    """
    # Process Invite Code
    job_role_id = None
    role_name = session_in.role
    if session_in.invite_code:
        job = db.query(JobRole).filter(JobRole.invite_code == session_in.invite_code).first()
        if not job:
            raise HTTPException(status_code=400, detail="Invalid invite code")
        job_role_id = job.id
        role_name = job.title

    resume = db.query(Resume).filter(Resume.user_id == current_user.id).order_by(Resume.created_at.desc()).first()
    resume_text = resume.extracted_text if resume else ""

    # Create session with status="generating"
    new_session = InterviewSession(
        user_id=current_user.id,
        role=role_name,
        job_role_id=job_role_id,
        job_description_id=session_in.job_description_id,
        difficulty=session_in.difficulty or "Medium",
        interview_type=session_in.interview_type or "Technical",
        status="generating"  # CHANGED: Mark as generating instead of pending
    )
    db.add(new_session)
    db.commit()
    db.refresh(new_session)

    # Queue background task to generate first question (no blocking)
    background_tasks.add_task(
        _generate_initial_question_bg,
        session_id=new_session.id,
        role=role_name,
        interview_type=new_session.interview_type,
        difficulty=new_session.difficulty,
        resume_text=resume_text,
        job_description_id=session_in.job_description_id
    )

    # Return immediately (session is in "generating" state)
    return new_session


@router.post("/retry", response_model=InterviewSessionResponse)
def retry_interview(
    session_in: InterviewSessionCreate,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    OPTIMIZED: Retry interview with same role/difficulty/type as previous session.
    Question generation runs in background (reduces latency from 2-3s to <100ms).
    """
    resume = db.query(Resume).filter(Resume.user_id == current_user.id).order_by(Resume.created_at.desc()).first()
    resume_text = resume.extracted_text if resume else ""

    # Create new session with status="generating"
    new_session = InterviewSession(
        user_id=current_user.id,
        role=session_in.role,
        job_description_id=session_in.job_description_id,
        difficulty=session_in.difficulty or "Medium",
        interview_type=session_in.interview_type or "Technical",
        status="generating"  # CHANGED: Mark as generating instead of pending
    )
    db.add(new_session)
    db.commit()
    db.refresh(new_session)

    # Queue background task to generate first question (no blocking)
    background_tasks.add_task(
        _generate_initial_question_bg,
        session_id=new_session.id,
        role=session_in.role,
        interview_type=new_session.interview_type,
        difficulty=new_session.difficulty,
        resume_text=resume_text,
        job_description_id=session_in.job_description_id
    )

    # Return immediately (session is in "generating" state)
    return new_session


@router.post("/generate-questions")
def generate_questions_only(
    session_in: InterviewSessionCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    resume = db.query(Resume).filter(Resume.user_id == current_user.id).order_by(Resume.created_at.desc()).first()
    if not resume:
        raise HTTPException(status_code=400, detail="Please upload a resume first.")

    question_texts = AIService.generate_questions(session_in.role, resume.extracted_text)
    return {"role": session_in.role, "questions": question_texts}


@router.get("/", response_model=List[InterviewSessionResponse])
def get_my_interviews(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    return db.query(InterviewSession).filter(
        InterviewSession.user_id == current_user.id
    ).order_by(InterviewSession.started_at.desc()).all()


@router.get("/{session_id}", response_model=InterviewSessionDetailed)
def get_interview_session(
    session_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    session = db.query(InterviewSession).filter(
        InterviewSession.id == session_id,
        InterviewSession.user_id == current_user.id
    ).first()

    if not session:
        raise HTTPException(status_code=404, detail="Interview session not found")

    return session


@router.get("/{session_id}/status")
def get_interview_status(
    session_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Check session readiness and get first question if available.
    Use this endpoint to poll until status="ready" after creating a session.
    """
    session = db.query(InterviewSession).filter(
        InterviewSession.id == session_id,
        InterviewSession.user_id == current_user.id
    ).first()

    if not session:
        raise HTTPException(status_code=404, detail="Interview session not found")

    # Get first question if session is ready
    first_question = None
    if session.status in ["ready", "in-progress", "completed"]:
        first_q = db.query(Question).filter(
            Question.session_id == session_id
        ).order_by(Question.created_at.asc()).first()
        if first_q:
            first_question = {
                "id": first_q.id,
                "text": first_q.question_text,
                "topic": first_q.topic,
                "difficulty": first_q.difficulty
            }

    return {
        "status": session.status,
        "first_question": first_question
    }


@router.get("/{session_id}/questions")
def get_interview_questions(
    session_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    session = db.query(InterviewSession).filter(
        InterviewSession.id == session_id,
        InterviewSession.user_id == current_user.id
    ).first()

    if not session:
        raise HTTPException(status_code=404, detail="Interview session not found")

    return session.questions


@router.get("/{session_id}/report")
def get_interview_report(
    session_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    session = db.query(InterviewSession).filter(
        InterviewSession.id == session_id,
        InterviewSession.user_id == current_user.id
    ).first()

    if not session or session.status != "completed":
        raise HTTPException(status_code=404, detail="Completed session not found")

    questions = db.query(Question).filter(Question.session_id == session_id).order_by(Question.id).all()

    ai_summary = ReportService.generate_ai_summary(session, questions)
    pdf_buffer = ReportService.create_pdf_report(session, questions, ai_summary)

    return Response(
        content=pdf_buffer.getvalue(),
        media_type="application/pdf",
        headers={
            "Content-Disposition": f"attachment; filename=interview_report_{session_id}.pdf"
        }
    )


@router.get("/{session_id}/feedback")
def get_interview_feedback(
    session_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    session = db.query(InterviewSession).filter(
        InterviewSession.id == session_id,
        InterviewSession.user_id == current_user.id
    ).first()

    if not session:
        raise HTTPException(status_code=404, detail="Interview session not found")

    return ReportService.generate_ai_summary(session, session.questions)
