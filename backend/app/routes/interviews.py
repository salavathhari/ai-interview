from fastapi import APIRouter, Depends, HTTPException, status, Response
from sqlalchemy.orm import Session
from typing import List
from app.database import get_db
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


@router.post("/", response_model=InterviewSessionResponse)
def create_interview_session(
    session_in: InterviewSessionCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
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

    jd_text = ""
    if session_in.job_description_id:
        jd = db.query(JobDescription).filter(
            JobDescription.id == session_in.job_description_id,
            JobDescription.user_id == current_user.id
        ).first()
        if jd:
            jd_text = jd.raw_text or ""

    new_session = InterviewSession(
        user_id=current_user.id,
        role=role_name,
        job_role_id=job_role_id,
        job_description_id=session_in.job_description_id,
        difficulty=session_in.difficulty or "Medium",
        interview_type=session_in.interview_type or "Technical",
        status="pending"
    )
    db.add(new_session)
    db.commit()
    db.refresh(new_session)

    initial_q_data = AIService.generate_next_question(
        role=role_name,
        interview_type=new_session.interview_type,
        difficulty=new_session.difficulty,
        resume_text=resume_text,
        previous_questions=[],
        weak_topics=[],
        strong_topics=[],
        jd_text=jd_text
    )
    db_q = Question(
        session_id=new_session.id,
        question_text=initial_q_data["text"],
        topic=initial_q_data.get("topic"),
        difficulty=initial_q_data.get("difficulty")
    )
    db.add(db_q)
    db.commit()

    return new_session


@router.post("/retry", response_model=InterviewSessionResponse)
def retry_interview(
    session_in: InterviewSessionCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Retry an interview with the same role/difficulty/type as a previous session.
    Creates a brand new session with fresh questions.
    """
    resume = db.query(Resume).filter(Resume.user_id == current_user.id).order_by(Resume.created_at.desc()).first()
    resume_text = resume.extracted_text if resume else ""

    jd_text = ""
    if session_in.job_description_id:
        jd = db.query(JobDescription).filter(
            JobDescription.id == session_in.job_description_id,
            JobDescription.user_id == current_user.id
        ).first()
        if jd:
            jd_text = jd.raw_text or ""

    new_session = InterviewSession(
        user_id=current_user.id,
        role=session_in.role,
        job_description_id=session_in.job_description_id,
        difficulty=session_in.difficulty or "Medium",
        interview_type=session_in.interview_type or "Technical",
        status="pending"
    )
    db.add(new_session)
    db.commit()
    db.refresh(new_session)

    initial_q_data = AIService.generate_next_question(
        role=session_in.role,
        interview_type=new_session.interview_type,
        difficulty=new_session.difficulty,
        resume_text=resume_text,
        previous_questions=[],
        weak_topics=[],
        strong_topics=[],
        jd_text=jd_text
    )
    db_q = Question(
        session_id=new_session.id,
        question_text=initial_q_data["text"],
        topic=initial_q_data.get("topic"),
        difficulty=initial_q_data.get("difficulty")
    )
    db.add(db_q)
    db.commit()

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
