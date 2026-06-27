from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import func
from app.database import get_db
from app.auth.utils import get_current_user
from app.models.user import User
from app.models.job_role import JobRole
from app.models.interview_session import InterviewSession
from app.models.question import Question
import uuid
from app.schemas.recruiter import JobRoleCreate, JobRoleResponse, RecruiterDashboard, CandidateSummary
from typing import List, Optional

router = APIRouter(
    prefix="/recruiter",
    tags=["recruiter"]
)

def verify_recruiter(current_user: User = Depends(get_current_user)):
    if not current_user.is_recruiter and not current_user.is_admin:
        raise HTTPException(status_code=403, detail="Recruiter access required")
    return current_user

@router.post("/jobs", response_model=JobRoleResponse)
def create_job(
    job_in: JobRoleCreate,
    recruiter: User = Depends(verify_recruiter),
    db: Session = Depends(get_db)
):
    job = JobRole(
        title=job_in.title,
        description=job_in.description,
        requirements=job_in.requirements,
        recruiter_id=recruiter.id,
        invite_code=str(uuid.uuid4())[:8].upper()
    )
    db.add(job)
    db.commit()
    db.refresh(job)
    return job

@router.get("/jobs", response_model=List[JobRoleResponse])
def list_jobs(
    recruiter: User = Depends(verify_recruiter),
    db: Session = Depends(get_db)
):
    return db.query(JobRole).filter(JobRole.recruiter_id == recruiter.id).all()

@router.get("/dashboard", response_model=RecruiterDashboard)
def get_recruiter_dashboard(
    recruiter: User = Depends(verify_recruiter),
    db: Session = Depends(get_db)
):
    jobs = db.query(JobRole).filter(JobRole.recruiter_id == recruiter.id).all()
    job_ids = [j.id for j in jobs]
    
    sessions = db.query(InterviewSession).filter(InterviewSession.job_role_id.in_(job_ids)).order_by(
        InterviewSession.score.desc().nullslast(),
        InterviewSession.started_at.desc()
    ).all()
    
    avg_score = db.query(func.avg(InterviewSession.score)).filter(
        InterviewSession.job_role_id.in_(job_ids),
        InterviewSession.status == "completed"
    ).scalar() or 0.0

    recent = []
    for rank, s in enumerate(sessions[:25], start=1):
        recent.append(CandidateSummary(
            user_email=s.user.email,
            user_name=s.user.name,
            score=s.score,
            status=s.status,
            started_at=s.started_at,
            session_id=s.id,
            rank=rank
        ))

    topic_rows = db.query(
        Question.topic,
        func.avg(Question.score).label("avg_score")
    ).join(InterviewSession).filter(
        InterviewSession.job_role_id.in_(job_ids),
        InterviewSession.status == "completed",
        Question.score.isnot(None),
        Question.topic.isnot(None)
    ).group_by(Question.topic).order_by(func.avg(Question.score).desc()).limit(5).all()
    strongest_skills = [row.topic for row in topic_rows]

    completed_count = len([s for s in sessions if s.status == "completed"])
    high_score_count = len([s for s in sessions if s.score is not None and s.score >= 8])
    hiring_recommendations = []
    if high_score_count:
        hiring_recommendations.append(f"Prioritize {high_score_count} candidate{'s' if high_score_count != 1 else ''} scoring 8.0+ for recruiter screen.")
    if avg_score >= 7.5:
        hiring_recommendations.append("Pipeline quality is strong; move top-ranked candidates into final technical rounds.")
    elif completed_count:
        hiring_recommendations.append("Average score suggests additional screening or a narrower role requirement set.")
    if strongest_skills:
        hiring_recommendations.append(f"Use {strongest_skills[0]} as a differentiating skill in panel interviews.")
    if not hiring_recommendations:
        hiring_recommendations.append("Collect more completed interviews before making hiring decisions.")

    return RecruiterDashboard(
        active_jobs=len(jobs),
        total_applicants=len(sessions),
        avg_candidate_score=float(avg_score),
        recent_candidates=recent,
        strongest_skills=strongest_skills,
        hiring_recommendations=hiring_recommendations
    )

@router.get("/jobs/{job_id}/candidates", response_model=List[CandidateSummary])
def get_job_candidates(
    job_id: int,
    recruiter: User = Depends(verify_recruiter),
    db: Session = Depends(get_db)
):
    job = db.query(JobRole).filter(JobRole.id == job_id, JobRole.recruiter_id == recruiter.id).first()
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
        
    sessions = db.query(InterviewSession).filter(InterviewSession.job_role_id == job_id).order_by(
        InterviewSession.score.desc().nullslast(),
        InterviewSession.started_at.desc()
    ).all()
    return [
        CandidateSummary(
            user_email=s.user.email,
            user_name=s.user.name,
            score=s.score,
            status=s.status,
            started_at=s.started_at,
            session_id=s.id,
            rank=rank
        ) for rank, s in enumerate(sessions, start=1)
    ]

@router.get("/jobs/{job_id}/rankings", response_model=List[CandidateSummary])
def get_job_rankings(
    job_id: int,
    recruiter: User = Depends(verify_recruiter),
    db: Session = Depends(get_db)
):
    """
    Step 17: Automatically rank candidates based on their total score.
    """
    job = db.query(JobRole).filter(JobRole.id == job_id, JobRole.recruiter_id == recruiter.id).first()
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
        
    # Order by score descending
    sessions = db.query(InterviewSession).filter(
        InterviewSession.job_role_id == job_id,
        InterviewSession.status == "completed"
    ).order_by(InterviewSession.score.desc()).all()
    
    return [
        CandidateSummary(
            user_email=s.user.email,
            user_name=s.user.name,
            score=s.score,
            status=s.status,
            started_at=s.started_at,
            session_id=s.id,
            rank=rank
        ) for rank, s in enumerate(sessions, start=1)
    ]
