"""
Candidate Job Board & Application Routes
Handles job discovery, application submission, tracking, and candidate assignments.
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import func, desc
from app.database import get_db
from app.auth.utils import get_current_user
from app.models.user import User
from app.models.recruiter import (
    RecruiterJobPost, Application, ApplicationHistory,
    Company, CandidateAssignment, Offer,
)
from app.models.job_role import JobRole
from app.models.resume import Resume
from app.models.career import ResumeAnalysis, SkillGapAnalysis, CareerReadiness
from app.models.interview_session import InterviewSession
from app.models.coding_challenge import CodingSession
from app.models.notification import Notification
from app.schemas.recruiter_v2 import (
    CandidateJobResponse, ApplicationSubmit, CandidateApplicationResponse,
    ApplicationTimelineEntry, AssignmentResponse,
)
from typing import List, Optional
from datetime import datetime, timezone


router = APIRouter(
    prefix="/candidate",
    tags=["candidate-jobs"]
)


def verify_candidate(current_user: User = Depends(get_current_user)):
    if current_user.is_admin:
        return current_user
    if current_user.is_recruiter:
        raise HTTPException(status_code=403, detail="Candidate access required")
    return current_user


# ═══════════════════════════════════════════════════════════════════════════════
# JOB DISCOVERY
# ═══════════════════════════════════════════════════════════════════════════════

@router.get("/jobs", response_model=dict)
def list_open_jobs(
    search: Optional[str] = None,
    location: Optional[str] = None,
    employment_type: Optional[str] = None,
    experience_level: Optional[str] = None,
    skills: Optional[str] = None,
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=100),
    candidate: User = Depends(verify_candidate),
    db: Session = Depends(get_db),
):
    """List all open jobs for candidates to browse."""
    query = db.query(RecruiterJobPost).filter(
        RecruiterJobPost.status == "open"
    )

    if search:
        from sqlalchemy import or_
        query = query.outerjoin(JobRole, JobRole.id == RecruiterJobPost.job_role_id).filter(
            or_(
                RecruiterJobPost.title.ilike(f"%{search}%"),
                JobRole.title.ilike(f"%{search}%"),
                RecruiterJobPost.description.ilike(f"%{search}%"),
                JobRole.description.ilike(f"%{search}%"),
            )
        )
    if location:
        query = query.filter(RecruiterJobPost.location.ilike(f"%{location}%"))
    if employment_type:
        query = query.filter(RecruiterJobPost.employment_type == employment_type)
    if experience_level:
        query = query.filter(RecruiterJobPost.experience_level == experience_level)

    total = query.count()
    jobs = query.order_by(desc(RecruiterJobPost.posted_at)).offset(
        (page - 1) * per_page
    ).limit(per_page).all()

    # Get user's active resume for ATS estimate
    active_resume = db.query(Resume).filter(
        Resume.user_id == candidate.id, Resume.is_active == True
    ).first()
    resume_analysis = None
    if active_resume:
        resume_analysis = db.query(ResumeAnalysis).filter(
            ResumeAnalysis.user_id == candidate.id
        ).order_by(desc(ResumeAnalysis.created_at)).first()

    career_readiness = db.query(CareerReadiness).filter(
        CareerReadiness.user_id == candidate.id
    ).first()

    # Check which jobs the candidate has already applied to
    applied_job_ids = set(
        row[0] for row in db.query(Application.job_post_id).filter(
            Application.user_id == candidate.id
        ).all()
    )

    job_list = []
    for job in jobs:
        company = db.query(Company).filter(Company.id == job.company_id).first() if job.company_id else None
        job_role = db.query(JobRole).filter(JobRole.id == job.job_role_id).first() if job.job_role_id else None
        title = job.title or (job_role.title if job_role else "Untitled")
        description = job.description or (job_role.description if job_role else None)
        job_list.append(CandidateJobResponse(
            id=job.id,
            title=title,
            description=description,
            company_name=company.name if company else None,
            company_logo=company.logo_url if company else None,
            department=job.department,
            location=job.location,
            employment_type=job.employment_type,
            experience_level=job.experience_level,
            salary_min=job.salary_min,
            salary_max=job.salary_max,
            salary_currency=job.salary_currency,
            required_skills=job.required_skills or [],
            preferred_skills=job.preferred_skills or [],
            education=job.education,
            responsibilities=job.responsibilities or [],
            benefits=job.benefits or [],
            deadline=job.deadline,
            posted_at=job.posted_at,
            created_at=job.created_at,
            has_applied=job.id in applied_job_ids,
            readiness_match=career_readiness.overall_score if career_readiness else None,
        ))

    return {"jobs": [j.model_dump() for j in job_list], "total": total, "page": page, "per_page": per_page}


@router.get("/jobs/{job_id}", response_model=CandidateJobResponse)
def get_job_detail(
    job_id: int,
    candidate: User = Depends(verify_candidate),
    db: Session = Depends(get_db),
):
    """Get detailed job posting for candidates."""
    job = db.query(RecruiterJobPost).filter(
        RecruiterJobPost.id == job_id,
        RecruiterJobPost.status == "open",
    ).first()
    if not job:
        raise HTTPException(status_code=404, detail="Job not found or not open")

    company = db.query(Company).filter(Company.id == job.company_id).first() if job.company_id else None
    job_role = db.query(JobRole).filter(JobRole.id == job.job_role_id).first() if job.job_role_id else None
    title = job.title or (job_role.title if job_role else "Untitled")
    description = job.description or (job_role.description if job_role else None)

    has_applied = db.query(Application).filter(
        Application.job_post_id == job_id,
        Application.user_id == candidate.id,
    ).first() is not None

    career_readiness = db.query(CareerReadiness).filter(
        CareerReadiness.user_id == candidate.id
    ).first()

    return CandidateJobResponse(
        id=job.id,
        title=title,
        description=description,
        company_name=company.name if company else None,
        company_logo=company.logo_url if company else None,
        department=job.department,
        location=job.location,
        employment_type=job.employment_type,
        experience_level=job.experience_level,
        salary_min=job.salary_min,
        salary_max=job.salary_max,
        salary_currency=job.salary_currency,
        required_skills=job.required_skills or [],
        preferred_skills=job.preferred_skills or [],
        education=job.education,
        responsibilities=job.responsibilities or [],
        benefits=job.benefits or [],
        deadline=job.deadline,
        posted_at=job.posted_at,
        created_at=job.created_at,
        has_applied=has_applied,
        readiness_match=career_readiness.overall_score if career_readiness else None,
    )


# ═══════════════════════════════════════════════════════════════════════════════
# APPLICATION SUBMISSION
# ═══════════════════════════════════════════════════════════════════════════════

@router.post("/jobs/{job_id}/apply", response_model=dict)
def apply_to_job(
    job_id: int,
    app_in: ApplicationSubmit,
    candidate: User = Depends(verify_candidate),
    db: Session = Depends(get_db),
):
    """Candidate applies to a job posting. Triggers auto-screening pipeline."""
    job = db.query(RecruiterJobPost).filter(
        RecruiterJobPost.id == job_id,
        RecruiterJobPost.status == "open",
    ).first()
    if not job:
        raise HTTPException(status_code=404, detail="Job not found or not open")

    # Check duplicate
    existing = db.query(Application).filter(
        Application.job_post_id == job_id,
        Application.user_id == candidate.id,
    ).first()
    if existing:
        raise HTTPException(status_code=400, detail="You have already applied to this job")

    # Verify resume exists and belongs to candidate
    resume = db.query(Resume).filter(
        Resume.id == app_in.resume_id,
        Resume.user_id == candidate.id,
    ).first()
    if not resume:
        raise HTTPException(status_code=400, detail="Resume not found")

    # Create application
    application = Application(
        job_post_id=job_id,
        user_id=candidate.id,
        recruiter_id=job.recruiter_id,
        resume_id=app_in.resume_id,
        cover_letter=app_in.cover_letter,
        source=app_in.source,
        status="applied",
    )
    db.add(application)
    db.commit()
    db.refresh(application)

    # Create history entry
    history = ApplicationHistory(
        application_id=application.id,
        from_stage=None,
        to_stage="applied",
        actor_id=candidate.id,
        actor_role="candidate",
    )
    db.add(history)
    db.commit()

    # Notify recruiter
    try:
        notif = Notification(
            user_id=job.recruiter_id,
            title="New Application Received",
            message=f"A candidate has applied for {job.title or 'a position'}",
            type="info",
        )
        db.add(notif)
        db.commit()
    except Exception:
        pass

    # Trigger auto-screening pipeline (non-blocking)
    try:
        _run_auto_screening(db, application, job)
    except Exception as e:
        print(f"Auto-screening failed for application {application.id}: {e}")

    return {
        "message": "Application submitted successfully",
        "application_id": application.id,
        "status": "applied",
    }


def _run_auto_screening(db: Session, application: Application, job: RecruiterJobPost):
    """Run automatic AI screening after application submission."""
    from app.models.career import ResumeAnalysis, SkillGapAnalysis, CareerReadiness

    user = db.query(User).filter(User.id == application.user_id).first()
    resume = db.query(Resume).filter(Resume.id == application.resume_id).first()
    if not user or not resume:
        return

    # Get latest resume analysis
    resume_analysis = db.query(ResumeAnalysis).filter(
        ResumeAnalysis.user_id == user.id
    ).order_by(desc(ResumeAnalysis.created_at)).first()

    if resume_analysis:
        application.resume_analysis_id = resume_analysis.id
        application.ats_score = resume_analysis.ats_score
        application.resume_match_score = resume_analysis.match_score

    # Get skill gap if exists
    skill_gap = db.query(SkillGapAnalysis).filter(
        SkillGapAnalysis.user_id == user.id
    ).order_by(desc(SkillGapAnalysis.created_at)).first()

    if skill_gap:
        application.skill_gap_score = getattr(skill_gap, 'overall_match_percentage', None)
        application.matched_skills = getattr(skill_gap, 'matching_skills', [])
        application.missing_skills = getattr(skill_gap, 'missing_skills', [])

    # Get career readiness
    readiness = db.query(CareerReadiness).filter(
        CareerReadiness.user_id == user.id
    ).first()

    if readiness:
        application.career_readiness_score = readiness.overall_score

    # Generate screening summary
    scores = []
    if application.ats_score:
        scores.append(f"ATS: {application.ats_score:.1f}")
    if application.resume_match_score:
        scores.append(f"Match: {application.resume_match_score:.1f}")
    if application.career_readiness_score:
        scores.append(f"Readiness: {application.career_readiness_score:.1f}")

    application.screening_summary = f"Auto-screened. Scores: {', '.join(scores)}" if scores else "Auto-screened. Awaiting manual review."
    application.screened_at = datetime.now(timezone.utc)

    # Update status to screening
    old_status = application.status
    application.status = "screening"

    history = ApplicationHistory(
        application_id=application.id,
        from_stage=old_status,
        to_stage="screening",
        actor_id=user.id,
        actor_role="system",
    )
    db.add(history)
    db.commit()


# ═══════════════════════════════════════════════════════════════════════════════
# CANDIDATE APPLICATION TRACKING
# ═══════════════════════════════════════════════════════════════════════════════

@router.get("/applications", response_model=dict)
def my_applications(
    status: Optional[str] = None,
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=100),
    candidate: User = Depends(verify_candidate),
    db: Session = Depends(get_db),
):
    """List candidate's applications with status."""
    try:
        return _my_applications_impl(status, page, per_page, candidate, db)
    except Exception as e:
        import traceback
        print(f"ERROR in my_applications: {e}")
        traceback.print_exc()
        raise


def _my_applications_impl(status, page, per_page, candidate, db):
    """List candidate's applications with status."""
    query = db.query(Application).filter(Application.user_id == candidate.id)
    if status:
        query = query.filter(Application.status == status)

    total = query.count()
    apps = query.order_by(desc(Application.applied_at)).offset(
        (page - 1) * per_page
    ).limit(per_page).all()

    result = []
    for app in apps:
        job = db.query(RecruiterJobPost).filter(RecruiterJobPost.id == app.job_post_id).first()
        company = db.query(Company).filter(Company.id == job.company_id).first() if job and job.company_id else None
        offer = db.query(Offer).filter(Offer.application_id == app.id).first()

        # Build timeline
        history = db.query(ApplicationHistory).filter(
            ApplicationHistory.application_id == app.id
        ).order_by(ApplicationHistory.created_at).all()

        timeline_stages = ["applied", "screening", "interview_scheduled", "interview_completed",
                          "coding_round", "selected", "offer_released", "hired"]
        current_idx = timeline_stages.index(app.status) if app.status in timeline_stages else -1

        timeline = []
        for i, stage in enumerate(timeline_stages):
            entry = next((h for h in history if h.to_stage == stage), None)
            timeline.append(ApplicationTimelineEntry(
                stage=stage,
                label=stage.replace("_", " ").title(),
                timestamp=entry.created_at if entry else None,
                actor=entry.actor_role if entry else None,
                note=entry.reason if entry else None,
                is_current=(i == current_idx),
            ).model_dump())

        result.append(CandidateApplicationResponse(
            id=app.id,
            job_title=job.title if job else "Unknown",
            company_name=company.name if company else None,
            status=app.status,
            applied_at=app.applied_at,
            updated_at=app.updated_at,
            timeline=timeline,
            ats_score=app.ats_score,
            resume_match_score=app.resume_match_score,
            career_readiness_score=app.career_readiness_score,
            interview_score=app.final_interview_score,
            coding_score=app.final_coding_score,
            decision=app.decision,
            decision_reason=app.decision_reason,
            offer={
                "id": offer.id,
                "salary_offered": offer.salary_offered,
                "currency": offer.currency,
                "status": offer.status,
                "position_title": offer.position_title,
            } if offer else None,
        ).model_dump())

    return {"applications": result, "total": total, "page": page, "per_page": per_page}


@router.get("/applications/{app_id}", response_model=CandidateApplicationResponse)
def my_application_detail(
    app_id: int,
    candidate: User = Depends(verify_candidate),
    db: Session = Depends(get_db),
):
    """Get detailed application status for candidate."""
    app = db.query(Application).filter(
        Application.id == app_id,
        Application.user_id == candidate.id,
    ).first()
    if not app:
        raise HTTPException(status_code=404, detail="Application not found")

    job = db.query(RecruiterJobPost).filter(RecruiterJobPost.id == app.job_post_id).first()
    company = db.query(Company).filter(Company.id == job.company_id).first() if job and job.company_id else None
    offer = db.query(Offer).filter(Offer.application_id == app.id).first()

    history = db.query(ApplicationHistory).filter(
        ApplicationHistory.application_id == app.id
    ).order_by(ApplicationHistory.created_at).all()

    timeline_stages = ["applied", "screening", "interview_scheduled", "interview_completed",
                      "coding_round", "selected", "offer_released", "hired"]
    current_idx = timeline_stages.index(app.status) if app.status in timeline_stages else -1

    timeline = []
    for i, stage in enumerate(timeline_stages):
        entry = next((h for h in history if h.to_stage == stage), None)
        timeline.append(ApplicationTimelineEntry(
            stage=stage,
            label=stage.replace("_", " ").title(),
            timestamp=entry.created_at if entry else None,
            actor=entry.actor_role if entry else None,
            note=entry.reason if entry else None,
            is_current=(i == current_idx),
        ).model_dump())

    return CandidateApplicationResponse(
        id=app.id,
        job_title=job.title if job else "Unknown",
        company_name=company.name if company else None,
        status=app.status,
        applied_at=app.applied_at,
        updated_at=app.updated_at,
        timeline=timeline,
        ats_score=app.ats_score,
        resume_match_score=app.resume_match_score,
        career_readiness_score=app.career_readiness_score,
        interview_score=app.final_interview_score,
        coding_score=app.final_coding_score,
        decision=app.decision,
        decision_reason=app.decision_reason,
        offer={
            "id": offer.id,
            "salary_offered": offer.salary_offered,
            "currency": offer.currency,
            "status": offer.status,
            "position_title": offer.position_title,
        } if offer else None,
    )


@router.post("/applications/{app_id}/withdraw")
def withdraw_application(
    app_id: int,
    candidate: User = Depends(verify_candidate),
    db: Session = Depends(get_db),
):
    """Candidate withdraws an application."""
    app = db.query(Application).filter(
        Application.id == app_id,
        Application.user_id == candidate.id,
    ).first()
    if not app:
        raise HTTPException(status_code=404, detail="Application not found")
    if app.status in ("hired", "withdrawn"):
        raise HTTPException(status_code=400, detail="Cannot withdraw this application")

    old_status = app.status
    app.status = "withdrawn"

    history = ApplicationHistory(
        application_id=app.id,
        from_stage=old_status,
        to_stage="withdrawn",
        reason="Candidate withdrew application",
        actor_id=candidate.id,
        actor_role="candidate",
    )
    db.add(history)
    db.commit()

    return {"message": "Application withdrawn"}


# ═══════════════════════════════════════════════════════════════════════════════
# CANDIDATE ASSIGNMENTS (Interview/Coding from Recruiter)
# ═══════════════════════════════════════════════════════════════════════════════

@router.get("/assignments", response_model=List[AssignmentResponse])
def my_assignments(
    status: Optional[str] = None,
    candidate: User = Depends(verify_candidate),
    db: Session = Depends(get_db),
):
    """List assignments (interview/coding) given to this candidate."""
    query = db.query(CandidateAssignment).filter(
        CandidateAssignment.assigned_to == candidate.id
    )
    if status:
        query = query.filter(CandidateAssignment.status == status)

    assignments = query.order_by(desc(CandidateAssignment.created_at)).all()
    return assignments


@router.get("/assignments/{assignment_id}", response_model=AssignmentResponse)
def my_assignment_detail(
    assignment_id: int,
    candidate: User = Depends(verify_candidate),
    db: Session = Depends(get_db),
):
    """Get assignment detail."""
    assignment = db.query(CandidateAssignment).filter(
        CandidateAssignment.id == assignment_id,
        CandidateAssignment.assigned_to == candidate.id,
    ).first()
    if not assignment:
        raise HTTPException(status_code=404, detail="Assignment not found")
    return assignment


@router.post("/assignments/{assignment_id}/start")
def start_assignment(
    assignment_id: int,
    candidate: User = Depends(verify_candidate),
    db: Session = Depends(get_db),
):
    """Candidate starts an assignment (interview or coding)."""
    assignment = db.query(CandidateAssignment).filter(
        CandidateAssignment.id == assignment_id,
        CandidateAssignment.assigned_to == candidate.id,
    ).first()
    if not assignment:
        raise HTTPException(status_code=404, detail="Assignment not found")
    if assignment.status != "pending":
        raise HTTPException(status_code=400, detail="Assignment already started or completed")

    assignment.status = "in_progress"
    db.commit()

    # Return the appropriate start URL/info
    if assignment.assignment_type == "interview":
        return {
            "type": "interview",
            "template_id": assignment.template_id,
            "message": "Use the interview setup page to start your interview",
            "start_url": "/interview-setup",
        }
    else:
        return {
            "type": "coding",
            "template_id": assignment.template_id,
            "message": "Use the coding page to start your assessment",
            "start_url": "/coding",
        }


# ═══════════════════════════════════════════════════════════════════════════════
# OFFER RESPONSE
# ═══════════════════════════════════════════════════════════════════════════════

@router.post("/offers/{offer_id}/respond")
def respond_to_offer(
    offer_id: int,
    body: dict,
    candidate: User = Depends(verify_candidate),
    db: Session = Depends(get_db),
):
    """Candidate accepts or rejects an offer."""
    offer = db.query(Offer).filter(Offer.id == offer_id).first()
    if not offer:
        raise HTTPException(status_code=404, detail="Offer not found")

    app = db.query(Application).filter(
        Application.id == offer.application_id,
        Application.user_id == candidate.id,
    ).first()
    if not app:
        raise HTTPException(status_code=403, detail="Access denied")

    if offer.status != "pending":
        raise HTTPException(status_code=400, detail="Offer is no longer pending")

    response = body.get("response")
    if response not in ("accepted", "rejected"):
        raise HTTPException(status_code=400, detail="Response must be 'accepted' or 'rejected'")

    offer.status = response
    offer.responded_at = datetime.now(timezone.utc)

    if response == "accepted":
        app.status = "hired"
        app.decision = "hired"
        app.decision_at = datetime.now(timezone.utc)
    elif response == "rejected":
        app.status = "rejected"
        app.decision = "rejected"
        app.decision_at = datetime.now(timezone.utc)
        app.decision_reason = "Candidate rejected offer"

    history = ApplicationHistory(
        application_id=app.id,
        from_stage="offer_released",
        to_stage="hired" if response == "accepted" else "rejected",
        reason=f"Candidate {response} the offer",
        actor_id=candidate.id,
        actor_role="candidate",
    )
    db.add(history)
    db.commit()

    # Notify recruiter
    try:
        notif = Notification(
            user_id=app.recruiter_id,
            title=f"Offer {response.title()}",
            message=f"Candidate has {response} the offer for the position",
            type="success" if response == "accepted" else "warning",
        )
        db.add(notif)
        db.commit()
    except Exception:
        pass

    return {"message": f"Offer {response}"}


# ═══════════════════════════════════════════════════════════════════════════════
# CANDIDATE NOTIFICATIONS
# ═══════════════════════════════════════════════════════════════════════════════

@router.get("/notifications")
def my_notifications(
    unread_only: bool = False,
    candidate: User = Depends(verify_candidate),
    db: Session = Depends(get_db),
):
    """Get candidate notifications."""
    query = db.query(Notification).filter(Notification.user_id == candidate.id)
    if unread_only:
        query = query.filter(Notification.is_read == False)
    notifications = query.order_by(desc(Notification.created_at)).limit(50).all()
    return {
        "notifications": [
            {
                "id": n.id,
                "title": n.title,
                "message": n.message,
                "type": n.type,
                "is_read": n.is_read,
                "created_at": n.created_at.isoformat() if n.created_at else None,
            }
            for n in notifications
        ]
    }


@router.patch("/notifications/{notif_id}/read")
def mark_notification_read(
    notif_id: int,
    candidate: User = Depends(verify_candidate),
    db: Session = Depends(get_db),
):
    """Mark a notification as read."""
    notif = db.query(Notification).filter(
        Notification.id == notif_id,
        Notification.user_id == candidate.id,
    ).first()
    if not notif:
        raise HTTPException(status_code=404, detail="Notification not found")
    notif.is_read = True
    db.commit()
    return {"message": "Marked as read"}


@router.patch("/notifications/read-all")
def mark_all_read(
    candidate: User = Depends(verify_candidate),
    db: Session = Depends(get_db),
):
    """Mark all notifications as read."""
    db.query(Notification).filter(
        Notification.user_id == candidate.id,
        Notification.is_read == False,
    ).update({"is_read": True})
    db.commit()
    return {"message": "All notifications marked as read"}
