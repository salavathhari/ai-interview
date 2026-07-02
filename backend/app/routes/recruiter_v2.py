"""
Recruiter Portal v2 — Full Production Router
All routes require recruiter JWT authorization via verify_recruiter dependency.
All write operations create a RecruiterActivity audit entry.
"""

import uuid
import json
from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session, selectinload
from sqlalchemy import func, desc, and_, or_
from app.database import get_db
from app.auth.utils import get_current_user
from app.models.user import User
from app.models.job_role import JobRole
from app.models.interview_session import InterviewSession
from app.models.question import Question
from app.models.interview_question_metric import InterviewQuestionMetric
from app.models.coding_challenge import CodingSession, CodingSubmission
from app.models.resume import Resume
from app.models.career import ResumeAnalysis, SkillGapAnalysis, CareerReadiness
from app.models.recruiter import (
    RecruiterJobPost, Application, ApplicationHistory,
    Shortlist, Offer, RecruiterActivity,
    InterviewTemplate, CodingTemplate,
)
from app.models.notification import Notification
from app.schemas.recruiter_v2 import (
    JobPostCreate, JobPostUpdate, JobPostResponse, JobPostListResponse,
    ApplicationCreate, ApplicationStageUpdate, ApplicationResponse,
    ApplicationListResponse, ApplicationHistoryResponse,
    CandidateProfileResponse,
    ShortlistAction, ShortlistResponse,
    OfferCreate, OfferResponse,
    InterviewTemplateCreate, InterviewTemplateUpdate, InterviewTemplateResponse,
    CodingTemplateCreate, CodingTemplateUpdate, CodingTemplateResponse,
    RecruiterDashboardV2, RecruiterAnalytics,
    CandidateComparison,
    RecruiterNotificationResponse, RecruiterActivityResponse,
)
from typing import List, Optional
from datetime import datetime, timezone


router = APIRouter(
    prefix="/recruiter/v2",
    tags=["recruiter-v2"]
)


# ─── Auth Dependency ──────────────────────────────────────────────────────────

def verify_recruiter(current_user: User = Depends(get_current_user)):
    if not current_user.is_recruiter and not current_user.is_admin:
        raise HTTPException(status_code=403, detail="Recruiter access required")
    return current_user


# ─── Helpers ─────────────────────────────────────────────────────────────────

def log_activity(db: Session, recruiter_id: int, action: str,
                 target_type: str = None, target_id: int = None, details: dict = None):
    activity = RecruiterActivity(
        recruiter_id=recruiter_id,
        action=action,
        target_type=target_type,
        target_id=target_id,
        details=details,
    )
    db.add(activity)
    db.commit()


def create_notification(db: Session, user_id: int, title: str, message: str, notif_type: str = "info"):
    notif = Notification(user_id=user_id, title=title, message=message, type=notif_type)
    db.add(notif)
    db.commit()


def _get_candidate_scores(db: Session, user_id: int, job_post_id: int = None):
    """Aggregate candidate scores from existing platform data."""
    scores = {}

    # Latest resume analysis
    ra = db.query(ResumeAnalysis).filter(ResumeAnalysis.user_id == user_id).order_by(
        ResumeAnalysis.created_at.desc()).first()
    if ra:
        scores["ats_score"] = ra.ats_score
        scores["resume_match"] = ra.resume_match_score

    # Interview score from sessions linked to recruiter's jobs
    query = db.query(InterviewSession).filter(
        InterviewSession.user_id == user_id,
        InterviewSession.status == "completed",
    )
    if job_post_id:
        job_post = db.query(RecruiterJobPost).filter(RecruiterJobPost.id == job_post_id).first()
        if job_post:
            query = query.filter(InterviewSession.job_role_id == job_post.job_role_id)
    latest_interview = query.order_by(InterviewSession.ended_at.desc()).first()
    if latest_interview:
        scores["interview_score"] = latest_interview.score

    # Coding score
    latest_coding = db.query(CodingSession).filter(
        CodingSession.user_id == user_id,
        CodingSession.status == "submitted",
    ).order_by(CodingSession.ended_at.desc()).first()
    if latest_coding:
        scores["coding_score"] = latest_coding.coding_score

    # Career readiness
    cr = db.query(CareerReadiness).filter(CareerReadiness.user_id == user_id).order_by(
        CareerReadiness.created_at.desc()).first()
    if cr:
        scores["career_readiness"] = cr.overall_score

    return scores


def _get_candidate_scores_batch(db: Session, user_ids: list) -> dict:
    """
    Batch retrieve candidate scores for multiple users (optimized - no N+1).
    Returns: {user_id: {ats_score, interview_score, coding_score, career_readiness}}
    """
    import traceback as _tb

    scores_by_user = {uid: {} for uid in user_ids}

    if not user_ids:
        return scores_by_user

    def _latest_per_user(model, score_col, order_col=None, filter_conditions=None):
        order = (order_col or model.created_at).desc()
        rn = func.row_number().over(
            partition_by=model.user_id,
            order_by=order
        ).label("rn")
        cols = [model.user_id, score_col.label("score"), rn]
        q = db.query(*cols)
        q = q.filter(model.user_id.in_(user_ids))
        if filter_conditions:
            for cond in filter_conditions:
                q = q.filter(cond)
        subq = q.subquery()
        return db.query(subq.c.user_id, subq.c.score).filter(subq.c.rn == 1).all()

    # Batch 1: Latest resume analysis per user
    rows = _latest_per_user(ResumeAnalysis, ResumeAnalysis.ats_score)
    for uid, score in rows:
        scores_by_user[uid]["ats_score"] = score

    rows = _latest_per_user(ResumeAnalysis, ResumeAnalysis.resume_match_score)
    for uid, score in rows:
        scores_by_user[uid]["resume_match"] = score

    # Batch 2: Latest completed interview session per user
    rows = _latest_per_user(
        InterviewSession, InterviewSession.score,
        order_col=InterviewSession.ended_at,
        filter_conditions=[InterviewSession.status == "completed"]
    )
    for uid, score in rows:
        scores_by_user[uid]["interview_score"] = score

    # Batch 3: Latest submitted coding session per user
    rows = _latest_per_user(
        CodingSession, CodingSession.coding_score,
        order_col=CodingSession.ended_at,
        filter_conditions=[CodingSession.status == "submitted"]
    )
    for uid, score in rows:
        scores_by_user[uid]["coding_score"] = score

    # Batch 4: Latest career readiness per user
    rows = _latest_per_user(CareerReadiness, CareerReadiness.overall_score)
    for uid, score in rows:
        scores_by_user[uid]["career_readiness"] = score

    return scores_by_user


# ═══════════════════════════════════════════════════════════════════════════════
# DASHBOARD
# ═══════════════════════════════════════════════════════════════════════════════

@router.get("/dashboard", response_model=RecruiterDashboardV2)
def get_dashboard(
    recruiter: User = Depends(verify_recruiter),
    db: Session = Depends(get_db)
):
    # Single query: Get all job posts with eager loading
    job_posts = db.query(RecruiterJobPost).filter(
        RecruiterJobPost.recruiter_id == recruiter.id
    ).all()
    job_post_ids = [jp.id for jp in job_posts]

    # Job counts by status
    open_jobs = len([j for j in job_posts if j.status == "open"])
    closed_jobs = len([j for j in job_posts if j.status == "closed"])
    draft_jobs = len([j for j in job_posts if j.status == "draft"])

    # Single query: Get all applications for these jobs with eager loading
    all_apps = db.query(Application).options(
        selectinload(Application.user)
    ).filter(Application.job_post_id.in_(job_post_ids)).all() if job_post_ids else []
    total_applications = len(all_apps)

    # Count by stage (no N queries, just dict counting)
    stage_counts = {}
    for app in all_apps:
        stage_counts[app.status] = stage_counts.get(app.status, 0) + 1

    # Batch: Get averages (single aggregation query per metric, not per app)
    avg_score = db.query(func.avg(InterviewSession.score)).filter(
        InterviewSession.job_role_id.in_([jp.job_role_id for jp in job_posts if jp.job_role_id]),
        InterviewSession.status == "completed"
    ).scalar() if job_posts else None

    avg_ats = db.query(func.avg(ResumeAnalysis.ats_score)).filter(
        ResumeAnalysis.user_id.in_([a.user_id for a in all_apps])
    ).scalar() if all_apps else None

    avg_readiness = db.query(func.avg(CareerReadiness.overall_score)).filter(
        CareerReadiness.user_id.in_([a.user_id for a in all_apps])
    ).scalar() if all_apps else None

    # Pipeline stages
    pipeline = [
        {"stage": "Applied", "count": stage_counts.get("applied", 0)},
        {"stage": "Screening", "count": stage_counts.get("screening", 0)},
        {"stage": "Interview", "count": stage_counts.get("interview_scheduled", 0) + stage_counts.get("interview_completed", 0)},
        {"stage": "Coding", "count": stage_counts.get("coding_round", 0)},
        {"stage": "Selected", "count": stage_counts.get("selected", 0)},
        {"stage": "Offer", "count": stage_counts.get("offer_released", 0)},
        {"stage": "Hired", "count": stage_counts.get("hired", 0)},
        {"stage": "Rejected", "count": stage_counts.get("rejected", 0)},
    ]

    # Recent activities (single query)
    activities = db.query(RecruiterActivity).filter(
        RecruiterActivity.recruiter_id == recruiter.id
    ).order_by(RecruiterActivity.created_at.desc()).limit(10).all()

    recent_activities = [
        {
            "id": a.id, "action": a.action, "target_type": a.target_type,
            "target_id": a.target_id, "details": a.details,
            "created_at": a.created_at.isoformat() if a.created_at else None,
        }
        for a in activities
    ]

    # Top candidates - OPTIMIZED: Get top 5 apps, then batch query scores
    top_candidates = []
    if all_apps:
        latest_apps = sorted(all_apps, key=lambda a: a.applied_at or datetime.min.replace(tzinfo=timezone.utc), reverse=True)[:5]
        candidate_user_ids = [app.user_id for app in latest_apps]
        
        # BATCH QUERY: Get all scores in 4 queries instead of per-user loops
        scores_by_user = _get_candidate_scores_batch(db, candidate_user_ids)
        
        for app in latest_apps:
            user = app.user if app.user else db.query(User).filter(User.id == app.user_id).first()
            scores = scores_by_user.get(app.user_id, {})
            top_candidates.append({
                "application_id": app.id,
                "user_id": app.user_id,
                "user_name": user.name if user else "Unknown",
                "user_email": user.email if user else "",
                "status": app.status,
                "scores": scores,
                "applied_at": app.applied_at.isoformat() if app.applied_at else None,
            })

    return RecruiterDashboardV2(
        total_jobs=len(job_posts),
        open_jobs=open_jobs,
        closed_jobs=closed_jobs,
        draft_jobs=draft_jobs,
        total_applications=total_applications,
        applications_in_screening=stage_counts.get("screening", 0),
        applications_in_interview=stage_counts.get("interview_scheduled", 0) + stage_counts.get("interview_completed", 0),
        applications_in_coding=stage_counts.get("coding_round", 0),
        shortlisted=stage_counts.get("selected", 0),
        rejected=stage_counts.get("rejected", 0),
        offers_released=stage_counts.get("offer_released", 0),
        hired=stage_counts.get("hired", 0),
        avg_candidate_score=float(avg_score) if avg_score else None,
        avg_ats_score=float(avg_ats) if avg_ats else None,
        avg_career_readiness=float(avg_readiness) if avg_readiness else None,
        pipeline=pipeline,
        recent_activities=recent_activities,
        top_candidates=top_candidates,
    )


@router.get("/analytics", response_model=RecruiterAnalytics)
def get_analytics(
    recruiter: User = Depends(verify_recruiter),
    db: Session = Depends(get_db)
):
    # Single query: Get all job posts
    job_posts = db.query(RecruiterJobPost).filter(
        RecruiterJobPost.recruiter_id == recruiter.id
    ).all()
    job_post_ids = [jp.id for jp in job_posts]

    # Single query: Get all applications
    all_apps = db.query(Application).filter(Application.job_post_id.in_(job_post_ids)).all() if job_post_ids else []

    # BATCH QUERY 1: Applications per job (single COUNT(*) GROUP BY instead of loop)
    apps_per_job_data = db.query(
        RecruiterJobPost.id,
        RecruiterJobPost.title,
        func.count(Application.id).label("count")
    ).outerjoin(Application, Application.job_post_id == RecruiterJobPost.id).filter(
        RecruiterJobPost.id.in_(job_post_ids)
    ).group_by(RecruiterJobPost.id, RecruiterJobPost.title).all()
    
    apps_per_job = [
        {"job_title": item.title or "Untitled", "count": item.count} 
        for item in apps_per_job_data
    ]

    # Hiring funnel
    stage_counts = {}
    for app in all_apps:
        stage_counts[app.status] = stage_counts.get(app.status, 0) + 1

    hiring_funnel = {
        "applied": stage_counts.get("applied", 0),
        "screening": stage_counts.get("screening", 0),
        "interview": stage_counts.get("interview_scheduled", 0) + stage_counts.get("interview_completed", 0),
        "coding": stage_counts.get("coding_round", 0),
        "selected": stage_counts.get("selected", 0),
        "offer": stage_counts.get("offer_released", 0),
        "hired": stage_counts.get("hired", 0),
        "rejected": stage_counts.get("rejected", 0),
    }

    # Average scores (single query per metric)
    avg_ats = db.query(func.avg(ResumeAnalysis.ats_score)).filter(
        ResumeAnalysis.user_id.in_([a.user_id for a in all_apps])
    ).scalar() if all_apps else 0

    avg_interview = db.query(func.avg(InterviewSession.score)).filter(
        InterviewSession.job_role_id.in_([jp.job_role_id for jp in job_posts if jp.job_role_id]),
        InterviewSession.status == "completed"
    ).scalar() if job_posts else 0

    avg_coding = db.query(func.avg(CodingSession.coding_score)).filter(
        CodingSession.user_id.in_([a.user_id for a in all_apps]),
        CodingSession.status == "submitted"
    ).scalar() if all_apps else 0

    avg_readiness = db.query(func.avg(CareerReadiness.overall_score)).filter(
        CareerReadiness.user_id.in_([a.user_id for a in all_apps])
    ).scalar() if all_apps else 0

    # BATCH QUERY 2: Source breakdown (single COUNT(*) GROUP BY instead of loop)
    source_data = db.query(
        Application.source,
        func.count(Application.id).label("count")
    ).filter(Application.id.in_([a.id for a in all_apps])).group_by(Application.source).all() if all_apps else []
    
    source_breakdown = [
        {"source": item.source or "unknown", "count": item.count} 
        for item in source_data
    ]

    # BATCH QUERY 3: Offer stats (single query combining both counts)
    offer_stats = db.query(
        func.count(Offer.id).label("total_offers"),
        func.count(func.case(
            (Offer.status == "accepted", 1),
            else_=None
        )).label("accepted_offers")
    ).filter(
        Offer.application_id.in_([a.id for a in all_apps])
    ).first() if all_apps else None
    
    total_offers = offer_stats.total_offers if offer_stats and offer_stats.total_offers else 0
    accepted_offers = offer_stats.accepted_offers if offer_stats and offer_stats.accepted_offers else 0

    acceptance_rate = (accepted_offers / total_offers * 100) if total_offers > 0 else 0
    offer_rate = (total_offers / len(all_apps) * 100) if all_apps else 0

    return RecruiterAnalytics(
        applications_per_job=apps_per_job,
        hiring_funnel=hiring_funnel,
        avg_scores={
            "ats": round(float(avg_ats), 1) if avg_ats else 0,
            "interview": round(float(avg_interview), 1) if avg_interview else 0,
            "coding": round(float(avg_coding), 1) if avg_coding else 0,
            "career_readiness": round(float(avg_readiness), 1) if avg_readiness else 0,
        },
        acceptance_rate=round(acceptance_rate, 1),
        offer_rate=round(offer_rate, 1),
        source_breakdown=source_breakdown,
    )


# ═══════════════════════════════════════════════════════════════════════════════
# JOBS
# ═══════════════════════════════════════════════════════════════════════════════

@router.get("/jobs", response_model=JobPostListResponse)
def list_jobs(
    status: Optional[str] = None,
    search: Optional[str] = None,
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=100),
    recruiter: User = Depends(verify_recruiter),
    db: Session = Depends(get_db)
):
    query = db.query(RecruiterJobPost).filter(RecruiterJobPost.recruiter_id == recruiter.id)

    if status:
        query = query.filter(RecruiterJobPost.status == status)
    if search:
        query = query.filter(RecruiterJobPost.title.ilike(f"%{search}%"))

    total = query.count()
    jobs = query.order_by(RecruiterJobPost.created_at.desc()).offset(
        (page - 1) * per_page
    ).limit(per_page).all()
    
    job_ids = [jp.id for jp in jobs]

    # BATCH QUERY 1: Get all application counts for these jobs
    app_counts = db.query(
        Application.job_post_id,
        func.count(Application.id).label("count")
    ).filter(Application.job_post_id.in_(job_ids)).group_by(Application.job_post_id).all()
    
    app_counts_map = {item.job_post_id: item.count for item in app_counts}
    
    # BATCH QUERY 2: Get all job roles (if not already on JobPost)
    job_role_ids = [jp.job_role_id for jp in jobs if jp.job_role_id]
    job_roles_map = {}
    if job_role_ids:
        job_roles = db.query(JobRole).filter(JobRole.id.in_(job_role_ids)).all()
        job_roles_map = {jr.id: jr for jr in job_roles}

    result = []
    for jp in jobs:
        app_count = app_counts_map.get(jp.id, 0)
        job_role = job_roles_map.get(jp.job_role_id) if jp.job_role_id else None
        result.append(JobPostResponse(
            id=jp.id,
            job_role_id=jp.job_role_id,
            recruiter_id=jp.recruiter_id,
            company_id=jp.company_id,
            title=jp.title or (job_role.title if job_role else "Untitled"),
            description=jp.description or (job_role.description if job_role else None),
            requirements=job_role.requirements if job_role else None,
            department=jp.department,
            location=jp.location,
            employment_type=jp.employment_type,
            experience_level=jp.experience_level,
            salary_min=jp.salary_min,
            salary_max=jp.salary_max,
            salary_currency=jp.salary_currency,
            required_skills=jp.required_skills or [],
            preferred_skills=jp.preferred_skills or [],
            education=jp.education,
            responsibilities=jp.responsibilities or [],
            benefits=jp.benefits or [],
            deadline=jp.deadline,
            interview_template_id=jp.interview_template_id,
            coding_template_id=jp.coding_template_id,
            status=jp.status,
            invite_code=job_role.invite_code if job_role else None,
            application_count=app_count,
            posted_at=jp.posted_at,
            created_at=jp.created_at,
            updated_at=jp.updated_at,
        ))

    return JobPostListResponse(jobs=result, total=total, page=page, per_page=per_page)


@router.post("/jobs", response_model=JobPostResponse)
def create_job(
    job_in: JobPostCreate,
    recruiter: User = Depends(verify_recruiter),
    db: Session = Depends(get_db)
):
    # Create the base JobRole first
    job_role = JobRole(
        title=job_in.title,
        description=job_in.description or "",
        requirements=job_in.requirements or "",
        recruiter_id=recruiter.id,
        invite_code=str(uuid.uuid4())[:8].upper(),
    )
    db.add(job_role)
    db.flush()

    # Create extended job post
    job_post = RecruiterJobPost(
        job_role_id=job_role.id,
        recruiter_id=recruiter.id,
        title=job_in.title,
        description=job_in.description,
        company_id=job_in.company_id,
        department=job_in.department,
        location=job_in.location,
        employment_type=job_in.employment_type,
        experience_level=job_in.experience_level,
        salary_min=job_in.salary_min,
        salary_max=job_in.salary_max,
        salary_currency=job_in.salary_currency,
        required_skills=job_in.required_skills or [],
        preferred_skills=job_in.preferred_skills or [],
        education=job_in.education,
        responsibilities=job_in.responsibilities or [],
        benefits=job_in.benefits or [],
        deadline=job_in.deadline,
        interview_template_id=job_in.interview_template_id,
        coding_template_id=job_in.coding_template_id,
        status=job_in.status or "draft",
        posted_at=datetime.now(timezone.utc) if job_in.status == "open" else None,
    )
    db.add(job_post)
    db.commit()
    db.refresh(job_post)

    log_activity(db, recruiter.id, "job_created", "job_post", job_post.id,
                 {"title": job_in.title, "status": job_post.status})

    return JobPostResponse(
        id=job_post.id,
        job_role_id=job_post.job_role_id,
        recruiter_id=job_post.recruiter_id,
        title=job_in.title,
        description=job_in.description,
        requirements=job_in.requirements,
        department=job_post.department,
        location=job_post.location,
        employment_type=job_post.employment_type,
        experience_level=job_post.experience_level,
        salary_min=job_post.salary_min,
        salary_max=job_post.salary_max,
        salary_currency=job_post.salary_currency,
        required_skills=job_post.required_skills or [],
        preferred_skills=job_post.preferred_skills or [],
        education=job_post.education,
        responsibilities=job_post.responsibilities or [],
        benefits=job_post.benefits or [],
        deadline=job_post.deadline,
        interview_template_id=job_post.interview_template_id,
        coding_template_id=job_post.coding_template_id,
        status=job_post.status,
        invite_code=job_role.invite_code,
        application_count=0,
        posted_at=job_post.posted_at,
        created_at=job_post.created_at,
    )


@router.get("/jobs/{job_id}", response_model=JobPostResponse)
def get_job(
    job_id: int,
    recruiter: User = Depends(verify_recruiter),
    db: Session = Depends(get_db)
):
    jp = db.query(RecruiterJobPost).filter(
        RecruiterJobPost.id == job_id,
        RecruiterJobPost.recruiter_id == recruiter.id,
    ).first()
    if not jp:
        raise HTTPException(status_code=404, detail="Job not found")

    job_role = db.query(JobRole).filter(JobRole.id == jp.job_role_id).first()
    app_count = db.query(Application).filter(Application.job_post_id == jp.id).count()

    return JobPostResponse(
        id=jp.id,
        job_role_id=jp.job_role_id,
        recruiter_id=jp.recruiter_id,
        title=job_role.title if job_role else jp.title or "Untitled",
        description=job_role.description if job_role else jp.description,
        requirements=job_role.requirements if job_role else None,
        department=jp.department,
        location=jp.location,
        employment_type=jp.employment_type,
        experience_level=jp.experience_level,
        salary_min=jp.salary_min,
        salary_max=jp.salary_max,
        salary_currency=jp.salary_currency,
        required_skills=jp.required_skills or [],
        preferred_skills=jp.preferred_skills or [],
        education=jp.education,
        responsibilities=jp.responsibilities or [],
        benefits=jp.benefits or [],
        deadline=jp.deadline,
        interview_template_id=jp.interview_template_id,
        coding_template_id=jp.coding_template_id,
        status=jp.status,
        invite_code=job_role.invite_code if job_role else None,
        application_count=app_count,
        posted_at=jp.posted_at,
        created_at=jp.created_at,
        updated_at=jp.updated_at,
    )


@router.put("/jobs/{job_id}", response_model=JobPostResponse)
def update_job(
    job_id: int,
    job_in: JobPostUpdate,
    recruiter: User = Depends(verify_recruiter),
    db: Session = Depends(get_db)
):
    jp = db.query(RecruiterJobPost).filter(
        RecruiterJobPost.id == job_id,
        RecruiterJobPost.recruiter_id == recruiter.id,
    ).first()
    if not jp:
        raise HTTPException(status_code=404, detail="Job not found")

    job_role = db.query(JobRole).filter(JobRole.id == jp.job_role_id).first()

    # Update fields
    update_data = job_in.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        if field in ("title", "description", "requirements") and job_role:
            setattr(job_role, field, value)
        elif hasattr(jp, field):
            setattr(jp, field, value)

    # Handle status change to "open"
    if job_in.status == "open" and jp.status != "open":
        jp.posted_at = datetime.now(timezone.utc)

    db.commit()
    db.refresh(jp)

    log_activity(db, recruiter.id, "job_updated", "job_post", jp.id,
                 {"title": job_role.title if job_role else None, "changes": list(update_data.keys())})

    return JobPostResponse(
        id=jp.id,
        job_role_id=jp.job_role_id,
        recruiter_id=jp.recruiter_id,
        title=job_role.title if job_role else jp.title or "Untitled",
        description=job_role.description if job_role else jp.description,
        requirements=job_role.requirements if job_role else None,
        department=jp.department,
        location=jp.location,
        employment_type=jp.employment_type,
        experience_level=jp.experience_level,
        salary_min=jp.salary_min,
        salary_max=jp.salary_max,
        salary_currency=jp.salary_currency,
        required_skills=jp.required_skills or [],
        preferred_skills=jp.preferred_skills or [],
        education=jp.education,
        responsibilities=jp.responsibilities or [],
        benefits=jp.benefits or [],
        deadline=jp.deadline,
        interview_template_id=jp.interview_template_id,
        coding_template_id=jp.coding_template_id,
        status=jp.status,
        invite_code=job_role.invite_code if job_role else None,
        posted_at=jp.posted_at,
        created_at=jp.created_at,
        updated_at=jp.updated_at,
    )


@router.patch("/jobs/{job_id}/status")
def update_job_status(
    job_id: int,
    body: dict,
    recruiter: User = Depends(verify_recruiter),
    db: Session = Depends(get_db)
):
    jp = db.query(RecruiterJobPost).filter(
        RecruiterJobPost.id == job_id,
        RecruiterJobPost.recruiter_id == recruiter.id,
    ).first()
    if not jp:
        raise HTTPException(status_code=404, detail="Job not found")

    new_status = body.get("status")
    if new_status not in ("draft", "open", "closed", "archived"):
        raise HTTPException(status_code=400, detail="Invalid status")

    old_status = jp.status
    jp.status = new_status
    if new_status == "open" and not jp.posted_at:
        jp.posted_at = datetime.now(timezone.utc)

    db.commit()

    log_activity(db, recruiter.id, "job_status_changed", "job_post", jp.id,
                 {"from": old_status, "to": new_status})

    return {"message": f"Job status changed to {new_status}"}


@router.delete("/jobs/{job_id}")
def delete_job(
    job_id: int,
    recruiter: User = Depends(verify_recruiter),
    db: Session = Depends(get_db)
):
    jp = db.query(RecruiterJobPost).filter(
        RecruiterJobPost.id == job_id,
        RecruiterJobPost.recruiter_id == recruiter.id,
    ).first()
    if not jp:
        raise HTTPException(status_code=404, detail="Job not found")

    job_role = db.query(JobRole).filter(JobRole.id == jp.job_role_id).first()

    log_activity(db, recruiter.id, "job_deleted", "job_post", jp.id,
                 {"title": job_role.title if job_role else None})

    # Delete applications and history first
    db.query(ApplicationHistory).filter(
        ApplicationHistory.application_id.in_(
            db.query(Application.id).filter(Application.job_post_id == jp.id)
        )
    ).delete(synchronize_session=False)
    db.query(Shortlist).filter(
        Shortlist.application_id.in_(
            db.query(Application.id).filter(Application.job_post_id == jp.id)
        )
    ).delete(synchronize_session=False)
    db.query(Offer).filter(
        Offer.application_id.in_(
            db.query(Application.id).filter(Application.job_post_id == jp.id)
        )
    ).delete(synchronize_session=False)
    db.query(Application).filter(Application.job_post_id == jp.id).delete()
    db.delete(jp)
    if job_role:
        db.delete(job_role)
    db.commit()

    return {"message": "Job deleted"}


@router.post("/jobs/{job_id}/duplicate", response_model=JobPostResponse)
def duplicate_job(
    job_id: int,
    recruiter: User = Depends(verify_recruiter),
    db: Session = Depends(get_db)
):
    jp = db.query(RecruiterJobPost).filter(
        RecruiterJobPost.id == job_id,
        RecruiterJobPost.recruiter_id == recruiter.id,
    ).first()
    if not jp:
        raise HTTPException(status_code=404, detail="Job not found")

    old_role = db.query(JobRole).filter(JobRole.id == jp.job_role_id).first()

    # Create new JobRole
    new_role = JobRole(
        title=f"{old_role.title} (Copy)" if old_role else "Untitled (Copy)",
        description=old_role.description if old_role else "",
        requirements=old_role.requirements if old_role else "",
        recruiter_id=recruiter.id,
        invite_code=str(uuid.uuid4())[:8].upper(),
    )
    db.add(new_role)
    db.flush()

    new_post = RecruiterJobPost(
        job_role_id=new_role.id,
        recruiter_id=recruiter.id,
        department=jp.department,
        location=jp.location,
        employment_type=jp.employment_type,
        experience_level=jp.experience_level,
        salary_min=jp.salary_min,
        salary_max=jp.salary_max,
        salary_currency=jp.salary_currency,
        required_skills=jp.required_skills,
        preferred_skills=jp.preferred_skills,
        education=jp.education,
        responsibilities=jp.responsibilities,
        benefits=jp.benefits,
        deadline=jp.deadline,
        interview_template_id=jp.interview_template_id,
        coding_template_id=jp.coding_template_id,
        status="draft",
    )
    db.add(new_post)
    db.commit()
    db.refresh(new_post)

    log_activity(db, recruiter.id, "job_duplicated", "job_post", new_post.id,
                 {"original_id": job_id, "title": new_role.title})

    return JobPostResponse(
        id=new_post.id,
        job_role_id=new_post.job_role_id,
        recruiter_id=new_post.recruiter_id,
        title=new_role.title,
        description=new_role.description,
        requirements=new_role.requirements,
        department=new_post.department,
        location=new_post.location,
        employment_type=new_post.employment_type,
        experience_level=new_post.experience_level,
        salary_min=new_post.salary_min,
        salary_max=new_post.salary_max,
        salary_currency=new_post.salary_currency,
        required_skills=new_post.required_skills or [],
        preferred_skills=new_post.preferred_skills or [],
        education=new_post.education,
        responsibilities=new_post.responsibilities or [],
        benefits=new_post.benefits or [],
        deadline=new_post.deadline,
        interview_template_id=new_post.interview_template_id,
        coding_template_id=new_post.coding_template_id,
        status=new_post.status,
        invite_code=new_role.invite_code,
        application_count=0,
        created_at=new_post.created_at,
    )


# ═══════════════════════════════════════════════════════════════════════════════
# APPLICATIONS
# ═══════════════════════════════════════════════════════════════════════════════

@router.get("/jobs/{job_id}/applications", response_model=ApplicationListResponse)
def list_job_applications(
    job_id: int,
    stage: Optional[str] = None,
    search: Optional[str] = None,
    score_min: Optional[float] = None,
    score_max: Optional[float] = None,
    source: Optional[str] = None,
    sort_by: Optional[str] = "applied_at",
    sort_order: Optional[str] = "desc",
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=100),
    recruiter: User = Depends(verify_recruiter),
    db: Session = Depends(get_db)
):
    jp = db.query(RecruiterJobPost).filter(
        RecruiterJobPost.id == job_id,
        RecruiterJobPost.recruiter_id == recruiter.id,
    ).first()
    if not jp:
        raise HTTPException(status_code=404, detail="Job not found")

    query = db.query(Application).filter(Application.job_post_id == job_id)

    if stage:
        query = query.filter(Application.status == stage)
    if source:
        query = query.filter(Application.source == source)
    if search:
        users = db.query(User).filter(
            User.name.ilike(f"%{search}%") | User.email.ilike(f"%{search}%")
        ).all()
        user_ids = [u.id for u in users]
        query = query.filter(Application.user_id.in_(user_ids))

    total = query.count()

    # BATCH: Stage counts for this job (single query)
    stage_counts_query = db.query(
        Application.status,
        func.count(Application.id).label("count")
    ).filter(Application.job_post_id == job_id).group_by(Application.status).all()
    
    stage_counts = {item.status: item.count for item in stage_counts_query}

    # Sort
    sort_col = getattr(Application, sort_by, Application.applied_at)
    if sort_order == "desc":
        query = query.order_by(sort_col.desc().nullslast())
    else:
        query = query.order_by(sort_col.asc().nullsfirst())

    apps = query.offset((page - 1) * per_page).limit(per_page).all()
    app_user_ids = [app.user_id for app in apps]
    
    # BATCH QUERY 1: Get all users
    users_map = {}
    if app_user_ids:
        users = db.query(User).filter(User.id.in_(app_user_ids)).all()
        users_map = {u.id: u for u in users}
    
    # BATCH QUERY 2: Get all candidate scores
    scores_by_user = _get_candidate_scores_batch(db, app_user_ids)

    result = []
    for app in apps:
        user = users_map.get(app.user_id)
        scores = scores_by_user.get(app.user_id, {})
        result.append(ApplicationResponse(
            id=app.id,
            job_post_id=app.job_post_id,
            user_id=app.user_id,
            user_name=user.name if user else "Unknown",
            user_email=user.email if user else "",
            status=app.status,
            resume_id=app.resume_id,
            cover_letter=app.cover_letter,
            source=app.source,
            ats_score=scores.get("ats_score"),
            resume_match=scores.get("resume_match"),
            interview_score=scores.get("interview_score"),
            coding_score=scores.get("coding_score"),
            career_readiness=scores.get("career_readiness"),
            applied_at=app.applied_at,
            updated_at=app.updated_at,
        ))

    return ApplicationListResponse(
        applications=result, total=total, page=page, per_page=per_page,
        stage_counts=stage_counts,
    )


@router.post("/jobs/{job_id}/applications", response_model=ApplicationResponse)
def create_application(
    job_id: int,
    app_in: ApplicationCreate,
    recruiter: User = Depends(verify_recruiter),
    db: Session = Depends(get_db)
):
    jp = db.query(RecruiterJobPost).filter(
        RecruiterJobPost.id == job_id,
        RecruiterJobPost.recruiter_id == recruiter.id,
    ).first()
    if not jp:
        raise HTTPException(status_code=404, detail="Job not found")

    # Check for duplicate
    existing = db.query(Application).filter(
        Application.job_post_id == job_id,
        Application.user_id == app_in.user_id,
    ).first()
    if existing:
        raise HTTPException(status_code=400, detail="Candidate already applied to this job")

    application = Application(
        job_post_id=job_id,
        user_id=app_in.user_id,
        resume_id=app_in.resume_id,
        cover_letter=app_in.cover_letter,
        source=app_in.source,
        status="applied",
    )
    db.add(application)
    db.commit()
    db.refresh(application)

    # Create history
    history = ApplicationHistory(
        application_id=application.id,
        from_stage=None,
        to_stage="applied",
        actor_id=recruiter.id,
        actor_role="recruiter",
    )
    db.add(history)
    db.commit()

    log_activity(db, recruiter.id, "application_created", "application", application.id,
                 {"job_id": job_id, "user_id": app_in.user_id})

    # Trigger automation
    try:
        from app.services.automation_service import AutomationService
        AutomationService(db).on_application_created(app_in.user_id, application.id)
    except Exception:
        pass

    # Notify recruiter
    user = db.query(User).filter(User.id == app_in.user_id).first()
    create_notification(db, recruiter.id, "New Application",
                       f"New application for {jp.title or 'a job'} from {user.name if user else 'a candidate'}")

    user = db.query(User).filter(User.id == app_in.user_id).first()
    scores = _get_candidate_scores(db, app_in.user_id, job_id)

    return ApplicationResponse(
        id=application.id,
        job_post_id=application.job_post_id,
        user_id=application.user_id,
        user_name=user.name if user else "Unknown",
        user_email=user.email if user else "",
        status=application.status,
        resume_id=application.resume_id,
        cover_letter=application.cover_letter,
        source=application.source,
        ats_score=scores.get("ats_score"),
        resume_match=scores.get("resume_match"),
        interview_score=scores.get("interview_score"),
        coding_score=scores.get("coding_score"),
        career_readiness=scores.get("career_readiness"),
        applied_at=application.applied_at,
    )


@router.get("/applications/{app_id}", response_model=ApplicationResponse)
def get_application(
    app_id: int,
    recruiter: User = Depends(verify_recruiter),
    db: Session = Depends(get_db)
):
    app = db.query(Application).filter(Application.id == app_id).first()
    if not app:
        raise HTTPException(status_code=404, detail="Application not found")

    jp = db.query(RecruiterJobPost).filter(
        RecruiterJobPost.id == app.job_post_id,
        RecruiterJobPost.recruiter_id == recruiter.id,
    ).first()
    if not jp:
        raise HTTPException(status_code=403, detail="Access denied")

    user = db.query(User).filter(User.id == app.user_id).first()
    scores = _get_candidate_scores(db, app.user_id, app.job_post_id)

    log_activity(db, recruiter.id, "application_viewed", "application", app.id)

    return ApplicationResponse(
        id=app.id,
        job_post_id=app.job_post_id,
        user_id=app.user_id,
        user_name=user.name if user else "Unknown",
        user_email=user.email if user else "",
        status=app.status,
        resume_id=app.resume_id,
        cover_letter=app.cover_letter,
        source=app.source,
        ats_score=scores.get("ats_score"),
        resume_match=scores.get("resume_match"),
        interview_score=scores.get("interview_score"),
        coding_score=scores.get("coding_score"),
        career_readiness=scores.get("career_readiness"),
        applied_at=app.applied_at,
        updated_at=app.updated_at,
    )


@router.patch("/applications/{app_id}/stage", response_model=ApplicationResponse)
def update_application_stage(
    app_id: int,
    stage_in: ApplicationStageUpdate,
    recruiter: User = Depends(verify_recruiter),
    db: Session = Depends(get_db)
):
    app = db.query(Application).filter(Application.id == app_id).first()
    if not app:
        raise HTTPException(status_code=404, detail="Application not found")

    jp = db.query(RecruiterJobPost).filter(
        RecruiterJobPost.id == app.job_post_id,
        RecruiterJobPost.recruiter_id == recruiter.id,
    ).first()
    if not jp:
        raise HTTPException(status_code=403, detail="Access denied")

    valid_stages = [
        "applied", "screening", "interview_scheduled", "interview_completed",
        "coding_round", "selected", "rejected", "offer_released", "hired", "withdrawn",
    ]
    if stage_in.status not in valid_stages:
        raise HTTPException(status_code=400, detail=f"Invalid stage. Must be one of: {valid_stages}")

    old_stage = app.status
    app.status = stage_in.status

    # Create history
    history = ApplicationHistory(
        application_id=app.id,
        from_stage=old_stage,
        to_stage=stage_in.status,
        reason=stage_in.reason,
        actor_id=recruiter.id,
        actor_role="recruiter",
    )
    db.add(history)
    db.commit()

    # Auto-create sessions when moving to interview or coding stage
    created_session_id = None
    if stage_in.status == "interview_scheduled" and not app.interview_session_id:
        template = None
        if jp.interview_template_id:
            template = db.query(InterviewTemplate).filter(
                InterviewTemplate.id == jp.interview_template_id,
                InterviewTemplate.recruiter_id == recruiter.id,
            ).first()
        session = InterviewSession(
            user_id=app.user_id,
            job_role_id=jp.job_role_id,
            role=jp.title or "Software Engineer",
            difficulty=template.difficulty if template else "Medium",
            interview_type=template.interview_type if template else "Technical",
            status="pending",
        )
        db.add(session)
        db.commit()
        db.refresh(session)
        app.interview_session_id = session.id
        db.commit()
        created_session_id = session.id
        log_activity(db, recruiter.id, "interview_auto_assigned", "application", app.id,
                     {"session_id": session.id})
        user_obj = db.query(User).filter(User.id == app.user_id).first()
        create_notification(db, app.user_id, "Interview Scheduled",
                            f"An interview has been scheduled for {jp.title or 'a position'}. Please check your dashboard.")

    elif stage_in.status == "coding_round" and not app.coding_session_id:
        template = None
        challenge_id = None
        if jp.coding_template_id:
            template = db.query(CodingTemplate).filter(
                CodingTemplate.id == jp.coding_template_id,
                CodingTemplate.recruiter_id == recruiter.id,
            ).first()
            if template and template.challenge_ids:
                challenge_id = template.challenge_ids[0]
        coding_session = CodingSession(
            user_id=app.user_id,
            challenge_id=challenge_id,
            status="in_progress",
        )
        db.add(coding_session)
        db.commit()
        db.refresh(coding_session)
        app.coding_session_id = coding_session.id
        db.commit()
        created_session_id = coding_session.id
        log_activity(db, recruiter.id, "coding_auto_assigned", "application", app.id,
                     {"coding_session_id": coding_session.id})
        user_obj = db.query(User).filter(User.id == app.user_id).first()
        create_notification(db, app.user_id, "Coding Round Assigned",
                            f"A coding assessment has been assigned for {jp.title or 'a position'}. Please check your dashboard.")

    log_activity(db, recruiter.id, "stage_changed", "application", app.id,
                 {"from": old_stage, "to": stage_in.status, "reason": stage_in.reason})

    # Trigger automation
    try:
        from app.services.automation_service import AutomationService
        AutomationService(db).on_application_stage_change(app.user_id, app.id, old_stage, stage_in.status)
    except Exception:
        pass

    user = db.query(User).filter(User.id == app.user_id).first()
    scores = _get_candidate_scores(db, app.user_id, app.job_post_id)

    return ApplicationResponse(
        id=app.id,
        job_post_id=app.job_post_id,
        user_id=app.user_id,
        user_name=user.name if user else "Unknown",
        user_email=user.email if user else "",
        status=app.status,
        resume_id=app.resume_id,
        cover_letter=app.cover_letter,
        source=app.source,
        ats_score=scores.get("ats_score"),
        resume_match=scores.get("resume_match"),
        interview_score=scores.get("interview_score"),
        coding_score=scores.get("coding_score"),
        career_readiness=scores.get("career_readiness"),
        applied_at=app.applied_at,
        updated_at=app.updated_at,
    )


@router.get("/applications/{app_id}/history", response_model=List[ApplicationHistoryResponse])
def get_application_history(
    app_id: int,
    recruiter: User = Depends(verify_recruiter),
    db: Session = Depends(get_db)
):
    app = db.query(Application).filter(Application.id == app_id).first()
    if not app:
        raise HTTPException(status_code=404, detail="Application not found")

    jp = db.query(RecruiterJobPost).filter(
        RecruiterJobPost.id == app.job_post_id,
        RecruiterJobPost.recruiter_id == recruiter.id,
    ).first()
    if not jp:
        raise HTTPException(status_code=403, detail="Access denied")

    history = db.query(ApplicationHistory).filter(
        ApplicationHistory.application_id == app_id
    ).order_by(ApplicationHistory.created_at.desc()).all()
    
    # BATCH: Get all recruiters for these history entries
    recruiter_ids = [h.recruiter_id for h in history if h.recruiter_id]
    recruiters_map = {}
    if recruiter_ids:
        recruiters = db.query(User).filter(User.id.in_(recruiter_ids)).all()
        recruiters_map = {r.id: r for r in recruiters}

    result = []
    for h in history:
        r = recruiters_map.get(h.recruiter_id)
        result.append(ApplicationHistoryResponse(
            id=h.id,
            application_id=h.application_id,
            from_stage=h.from_stage,
            to_stage=h.to_stage,
            reason=h.reason,
            recruiter_id=h.recruiter_id,
            recruiter_name=r.name if r else "Unknown",
            created_at=h.created_at,
        ))

    return result


# ═══════════════════════════════════════════════════════════════════════════════
# CANDIDATE PROFILE
# ═══════════════════════════════════════════════════════════════════════════════

@router.get("/candidates/{user_id}/profile", response_model=CandidateProfileResponse)
def get_candidate_profile(
    user_id: int,
    recruiter: User = Depends(verify_recruiter),
    db: Session = Depends(get_db)
):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="Candidate not found")

    # Verify recruiter has access (has application from this candidate)
    recruiter_jobs = db.query(RecruiterJobPost).filter(
        RecruiterJobPost.recruiter_id == recruiter.id
    ).all()
    job_post_ids = [jp.id for jp in recruiter_jobs]

    has_access = db.query(Application).filter(
        Application.job_post_id.in_(job_post_ids),
        Application.user_id == user_id,
    ).first()
    if not has_access and not recruiter.is_admin:
        raise HTTPException(status_code=403, detail="Access denied")

    # Resume
    resume = db.query(Resume).filter(Resume.user_id == user_id).order_by(
        Resume.created_at.desc()).first()
    resume_data = None
    if resume:
        resume_data = {
            "id": resume.id, "filename": resume.filename,
            "skills": resume.skills, "created_at": resume.created_at.isoformat() if resume.created_at else None,
        }

    # Resume analysis
    ra = db.query(ResumeAnalysis).filter(ResumeAnalysis.user_id == user_id).order_by(
        ResumeAnalysis.created_at.desc()).first()
    ra_data = None
    if ra:
        ra_data = {
            "id": ra.id, "ats_score": ra.ats_score, "resume_match_score": ra.resume_match_score,
            "detected_skills": ra.detected_skills, "experience_level": ra.experience_level,
        }

    # Interview scores
    interviews = db.query(InterviewSession).filter(
        InterviewSession.user_id == user_id,
        InterviewSession.status == "completed",
    ).order_by(InterviewSession.ended_at.desc()).limit(10).all()
    interview_scores = [
        {
            "id": s.id, "role": s.role, "score": s.score, "difficulty": s.difficulty,
            "interview_type": s.interview_type,
            "score_dsa": s.score_dsa, "score_dbms": s.score_dbms, "score_os": s.score_os,
            "score_cn": s.score_cn, "score_oop": s.score_oop,
            "started_at": s.started_at.isoformat() if s.started_at else None,
        }
        for s in interviews
    ]

    # Coding scores
    coding_sessions = db.query(CodingSession).filter(
        CodingSession.user_id == user_id,
        CodingSession.status == "submitted",
    ).order_by(CodingSession.ended_at.desc()).limit(10).all()
    coding_scores = [
        {
            "id": s.id, "coding_score": s.coding_score, "language_used": s.language_used,
            "started_at": s.started_at.isoformat() if s.started_at else None,
        }
        for s in coding_sessions
    ]

    # Career readiness
    cr = db.query(CareerReadiness).filter(CareerReadiness.user_id == user_id).order_by(
        CareerReadiness.created_at.desc()).first()
    cr_data = None
    if cr:
        cr_data = {
            "overall_score": cr.overall_score, "resume_match_score": cr.resume_match_score,
            "ats_score": cr.ats_score, "interview_score": cr.interview_score,
            "coding_score": cr.coding_score, "skill_gap_score": cr.skill_gap_score,
            "learning_score": cr.learning_score, "project_score": cr.project_score,
        }

    # Skill gap
    sg = db.query(SkillGapAnalysis).filter(SkillGapAnalysis.user_id == user_id).order_by(
        SkillGapAnalysis.created_at.desc()).first()
    sg_data = None
    if sg:
        sg_data = {
            "match_percentage": sg.match_percentage,
            "matched_skills": sg.matched_skills, "missing_skills": sg.missing_skills,
        }

    # Applications
    apps = db.query(Application).filter(
        Application.user_id == user_id,
        Application.job_post_id.in_(job_post_ids),
    ).all() if job_post_ids else []
    app_data = [
        {
            "id": a.id, "job_post_id": a.job_post_id, "status": a.status,
            "applied_at": a.applied_at.isoformat() if a.applied_at else None,
        }
        for a in apps
    ]

    return CandidateProfileResponse(
        user_id=user_id,
        name=user.name,
        email=user.email,
        resume=resume_data,
        resume_analysis=ra_data,
        interview_scores=interview_scores,
        coding_scores=coding_scores,
        career_readiness=cr_data,
        skill_gap=sg_data,
        applications=app_data,
    )


# ═══════════════════════════════════════════════════════════════════════════════
# SHORTLISTING
# ═══════════════════════════════════════════════════════════════════════════════

@router.post("/applications/{app_id}/shortlist", response_model=ShortlistResponse)
def shortlist_application(
    app_id: int,
    action_in: ShortlistAction,
    recruiter: User = Depends(verify_recruiter),
    db: Session = Depends(get_db)
):
    app = db.query(Application).filter(Application.id == app_id).first()
    if not app:
        raise HTTPException(status_code=404, detail="Application not found")

    jp = db.query(RecruiterJobPost).filter(
        RecruiterJobPost.id == app.job_post_id,
        RecruiterJobPost.recruiter_id == recruiter.id,
    ).first()
    if not jp:
        raise HTTPException(status_code=403, detail="Access denied")

    if action_in.action not in ("shortlist", "reject", "hold"):
        raise HTTPException(status_code=400, detail="Invalid action")

    shortlist = Shortlist(
        application_id=app_id,
        recruiter_id=recruiter.id,
        action=action_in.action,
        reason=action_in.reason,
        comments=action_in.comments,
    )
    db.add(shortlist)

    # Update application status based on action
    if action_in.action == "shortlist":
        app.status = "selected"
    elif action_in.action == "reject":
        app.status = "rejected"

    # Create history
    history = ApplicationHistory(
        application_id=app_id,
        from_stage=app.status,
        to_stage=app.status,
        reason=f"Shortlist action: {action_in.action}. {action_in.reason or ''}",
        actor_id=recruiter.id,
        actor_role="recruiter",
    )
    db.add(history)
    db.commit()
    db.refresh(shortlist)

    log_activity(db, recruiter.id, f"application_{action_in.action}ed", "application", app_id,
                 {"reason": action_in.reason, "comments": action_in.comments})

    return ShortlistResponse(
        id=shortlist.id,
        application_id=shortlist.application_id,
        recruiter_id=shortlist.recruiter_id,
        action=shortlist.action,
        reason=shortlist.reason,
        comments=shortlist.comments,
        created_at=shortlist.created_at,
    )


@router.get("/jobs/{job_id}/shortlists", response_model=List[ShortlistResponse])
def get_job_shortlists(
    job_id: int,
    recruiter: User = Depends(verify_recruiter),
    db: Session = Depends(get_db)
):
    jp = db.query(RecruiterJobPost).filter(
        RecruiterJobPost.id == job_id,
        RecruiterJobPost.recruiter_id == recruiter.id,
    ).first()
    if not jp:
        raise HTTPException(status_code=404, detail="Job not found")

    # OPTIMIZED: Single query using subquery instead of fetching all applications
    shortlists = db.query(Shortlist).filter(
        Shortlist.application_id.in_(
            db.query(Application.id).filter(Application.job_post_id == job_id)
        )
    ).order_by(Shortlist.created_at.desc()).all()

    return [
        ShortlistResponse(
            id=s.id, application_id=s.application_id, recruiter_id=s.recruiter_id,
            action=s.action, reason=s.reason, comments=s.comments, created_at=s.created_at,
        )
        for s in shortlists
    ]


# ═══════════════════════════════════════════════════════════════════════════════
# OFFERS
# ═══════════════════════════════════════════════════════════════════════════════

@router.post("/applications/{app_id}/offer", response_model=OfferResponse)
def create_offer(
    app_id: int,
    offer_in: OfferCreate,
    recruiter: User = Depends(verify_recruiter),
    db: Session = Depends(get_db)
):
    app = db.query(Application).filter(Application.id == app_id).first()
    if not app:
        raise HTTPException(status_code=404, detail="Application not found")

    jp = db.query(RecruiterJobPost).filter(
        RecruiterJobPost.id == app.job_post_id,
        RecruiterJobPost.recruiter_id == recruiter.id,
    ).first()
    if not jp:
        raise HTTPException(status_code=403, detail="Access denied")

    offer = Offer(
        application_id=app_id,
        recruiter_id=recruiter.id,
        salary_offered=offer_in.salary_offered,
        currency=offer_in.currency,
        benefits=offer_in.benefits or [],
        notes=offer_in.notes,
        expires_at=offer_in.expires_at,
        status="pending",
    )
    db.add(offer)

    app.status = "offer_released"

    history = ApplicationHistory(
        application_id=app_id,
        from_stage="selected",
        to_stage="offer_released",
        reason="Offer created",
        actor_id=recruiter.id,
        actor_role="recruiter",
    )
    db.add(history)
    db.commit()
    db.refresh(offer)

    log_activity(db, recruiter.id, "offer_created", "offer", offer.id,
                 {"application_id": app_id, "salary": offer_in.salary_offered})

    # Trigger automation
    try:
        from app.services.automation_service import AutomationService
        AutomationService(db).on_offer_event(app.user_id, offer.id, "created")
    except Exception:
        pass

    user = db.query(User).filter(User.id == app.user_id).first()
    create_notification(db, recruiter.id, "Offer Created",
                       f"Offer created for {user.name if user else 'candidate'} for {jp.title or 'a position'}")

    return OfferResponse(
        id=offer.id,
        application_id=offer.application_id,
        recruiter_id=offer.recruiter_id,
        candidate_name=user.name if user else "Unknown",
        job_title=jp.title if jp else None,
        salary_offered=offer.salary_offered,
        currency=offer.currency,
        benefits=offer.benefits or [],
        status=offer.status,
        notes=offer.notes,
        expires_at=offer.expires_at,
        created_at=offer.created_at,
    )


@router.get("/offers", response_model=List[OfferResponse])
def list_offers(
    recruiter: User = Depends(verify_recruiter),
    db: Session = Depends(get_db)
):
    offers = db.query(Offer).filter(
        Offer.recruiter_id == recruiter.id
    ).order_by(Offer.created_at.desc()).all()
    
    offer_app_ids = [o.application_id for o in offers]
    
    # BATCH QUERY 1: Get all applications
    apps_map = {}
    if offer_app_ids:
        apps = db.query(Application).filter(Application.id.in_(offer_app_ids)).all()
        apps_map = {a.id: a for a in apps}
    
    # Extract all user_ids and job_post_ids from applications
    user_ids = [a.user_id for a in apps_map.values() if a.user_id]
    job_post_ids = [a.job_post_id for a in apps_map.values() if a.job_post_id]
    
    # BATCH QUERY 2: Get all users
    users_map = {}
    if user_ids:
        users = db.query(User).filter(User.id.in_(user_ids)).all()
        users_map = {u.id: u for u in users}
    
    # BATCH QUERY 3: Get all job posts
    job_posts_map = {}
    if job_post_ids:
        job_posts = db.query(RecruiterJobPost).filter(RecruiterJobPost.id.in_(job_post_ids)).all()
        job_posts_map = {jp.id: jp for jp in job_posts}

    result = []
    for o in offers:
        app = apps_map.get(o.application_id)
        user = users_map.get(app.user_id) if app else None
        jp = job_posts_map.get(app.job_post_id) if app else None
        result.append(OfferResponse(
            id=o.id, application_id=o.application_id, recruiter_id=o.recruiter_id,
            candidate_name=user.name if user else "Unknown",
            job_title=jp.title if jp else None,
            salary_offered=o.salary_offered, currency=o.currency,
            benefits=o.benefits or [], status=o.status, notes=o.notes,
            expires_at=o.expires_at, responded_at=o.responded_at,
            created_at=o.created_at,
        ))

    return result


@router.patch("/offers/{offer_id}/status")
def update_offer_status(
    offer_id: int,
    body: dict,
    recruiter: User = Depends(verify_recruiter),
    db: Session = Depends(get_db)
):
    offer = db.query(Offer).filter(Offer.id == offer_id).first()
    if not offer:
        raise HTTPException(status_code=404, detail="Offer not found")

    jp = db.query(RecruiterJobPost).filter(
        RecruiterJobPost.id == db.query(Application.job_post_id).filter(Application.id == offer.application_id).scalar()
    ).first()
    if not jp or jp.recruiter_id != recruiter.id:
        raise HTTPException(status_code=403, detail="Access denied")

    new_status = body.get("status")
    if new_status not in ("accepted", "rejected", "expired"):
        raise HTTPException(status_code=400, detail="Invalid status")

    offer.status = new_status
    offer.responded_at = datetime.now(timezone.utc)

    if new_status == "accepted":
        app = db.query(Application).filter(Application.id == offer.application_id).first()
        if app:
            app.status = "hired"

    db.commit()

    log_activity(db, recruiter.id, f"offer_{new_status}", "offer", offer_id)

    # Trigger automation
    try:
        from app.services.automation_service import AutomationService
        app = db.query(Application).filter(Application.id == offer.application_id).first()
        if app:
            AutomationService(db).on_offer_event(app.user_id, offer_id, new_status)
    except Exception:
        pass

    return {"message": f"Offer {new_status}"}


# ═══════════════════════════════════════════════════════════════════════════════
# REPORTS
# ═══════════════════════════════════════════════════════════════════════════════

@router.get("/reports/hiring-pdf")
def download_hiring_report(
    recruiter: User = Depends(verify_recruiter),
    db: Session = Depends(get_db)
):
    from app.services.report_service import generate_recruiter_hiring_report
    buffer = generate_recruiter_hiring_report(db, recruiter.id)
    return StreamingResponse(
        buffer,
        media_type="application/pdf",
        headers={"Content-Disposition": f"attachment; filename=hiring-report-{recruiter.id}.pdf"},
    )


# ═══════════════════════════════════════════════════════════════════════════════
# TEMPLATES
# ═══════════════════════════════════════════════════════════════════════════════

@router.get("/templates/interviews", response_model=List[InterviewTemplateResponse])
def list_interview_templates(
    recruiter: User = Depends(verify_recruiter),
    db: Session = Depends(get_db)
):
    templates = db.query(InterviewTemplate).filter(
        InterviewTemplate.recruiter_id == recruiter.id
    ).order_by(InterviewTemplate.created_at.desc()).all()
    return templates


@router.post("/templates/interviews", response_model=InterviewTemplateResponse)
def create_interview_template(
    tmpl_in: InterviewTemplateCreate,
    recruiter: User = Depends(verify_recruiter),
    db: Session = Depends(get_db)
):
    template = InterviewTemplate(
        recruiter_id=recruiter.id,
        name=tmpl_in.name,
        description=tmpl_in.description,
        role=tmpl_in.role,
        difficulty=tmpl_in.difficulty,
        interview_type=tmpl_in.interview_type,
        topics=tmpl_in.topics or [],
        num_questions=tmpl_in.num_questions,
        time_limit_min=tmpl_in.time_limit_min,
    )
    db.add(template)
    db.commit()
    db.refresh(template)

    log_activity(db, recruiter.id, "template_created", "interview_template", template.id)

    return template


@router.put("/templates/interviews/{tmpl_id}", response_model=InterviewTemplateResponse)
def update_interview_template(
    tmpl_id: int,
    tmpl_in: InterviewTemplateUpdate,
    recruiter: User = Depends(verify_recruiter),
    db: Session = Depends(get_db)
):
    template = db.query(InterviewTemplate).filter(
        InterviewTemplate.id == tmpl_id,
        InterviewTemplate.recruiter_id == recruiter.id,
    ).first()
    if not template:
        raise HTTPException(status_code=404, detail="Template not found")

    for field, value in tmpl_in.model_dump(exclude_unset=True).items():
        setattr(template, field, value)

    db.commit()
    db.refresh(template)
    return template


@router.delete("/templates/interviews/{tmpl_id}")
def delete_interview_template(
    tmpl_id: int,
    recruiter: User = Depends(verify_recruiter),
    db: Session = Depends(get_db)
):
    template = db.query(InterviewTemplate).filter(
        InterviewTemplate.id == tmpl_id,
        InterviewTemplate.recruiter_id == recruiter.id,
    ).first()
    if not template:
        raise HTTPException(status_code=404, detail="Template not found")

    db.delete(template)
    db.commit()
    return {"message": "Template deleted"}


@router.get("/templates/coding", response_model=List[CodingTemplateResponse])
def list_coding_templates(
    recruiter: User = Depends(verify_recruiter),
    db: Session = Depends(get_db)
):
    templates = db.query(CodingTemplate).filter(
        CodingTemplate.recruiter_id == recruiter.id
    ).order_by(CodingTemplate.created_at.desc()).all()
    return templates


@router.post("/templates/coding", response_model=CodingTemplateResponse)
def create_coding_template(
    tmpl_in: CodingTemplateCreate,
    recruiter: User = Depends(verify_recruiter),
    db: Session = Depends(get_db)
):
    template = CodingTemplate(
        recruiter_id=recruiter.id,
        name=tmpl_in.name,
        description=tmpl_in.description,
        difficulty=tmpl_in.difficulty,
        challenge_ids=tmpl_in.challenge_ids or [],
        time_limit_min=tmpl_in.time_limit_min,
    )
    db.add(template)
    db.commit()
    db.refresh(template)

    log_activity(db, recruiter.id, "template_created", "coding_template", template.id)

    return template


@router.put("/templates/coding/{tmpl_id}", response_model=CodingTemplateResponse)
def update_coding_template(
    tmpl_id: int,
    tmpl_in: CodingTemplateUpdate,
    recruiter: User = Depends(verify_recruiter),
    db: Session = Depends(get_db)
):
    template = db.query(CodingTemplate).filter(
        CodingTemplate.id == tmpl_id,
        CodingTemplate.recruiter_id == recruiter.id,
    ).first()
    if not template:
        raise HTTPException(status_code=404, detail="Template not found")

    for field, value in tmpl_in.model_dump(exclude_unset=True).items():
        setattr(template, field, value)

    db.commit()
    db.refresh(template)
    return template


@router.delete("/templates/coding/{tmpl_id}")
def delete_coding_template(
    tmpl_id: int,
    recruiter: User = Depends(verify_recruiter),
    db: Session = Depends(get_db)
):
    template = db.query(CodingTemplate).filter(
        CodingTemplate.id == tmpl_id,
        CodingTemplate.recruiter_id == recruiter.id,
    ).first()
    if not template:
        raise HTTPException(status_code=404, detail="Template not found")

    db.delete(template)
    db.commit()
    return {"message": "Template deleted"}


# ═══════════════════════════════════════════════════════════════════════════════
# INTERVIEW / CODING ASSIGNMENT
# ═══════════════════════════════════════════════════════════════════════════════

@router.post("/applications/{app_id}/assign-interview")
def assign_interview(
    app_id: int,
    body: dict = None,
    recruiter: User = Depends(verify_recruiter),
    db: Session = Depends(get_db)
):
    app = db.query(Application).filter(Application.id == app_id).first()
    if not app:
        raise HTTPException(status_code=404, detail="Application not found")

    jp = db.query(RecruiterJobPost).filter(
        RecruiterJobPost.id == app.job_post_id,
        RecruiterJobPost.recruiter_id == recruiter.id,
    ).first()
    if not jp:
        raise HTTPException(status_code=403, detail="Access denied")

    # Get template if specified
    template = None
    if body and body.get("template_id"):
        template = db.query(InterviewTemplate).filter(
            InterviewTemplate.id == body["template_id"],
            InterviewTemplate.recruiter_id == recruiter.id,
        ).first()

    # Create interview session
    session = InterviewSession(
        user_id=app.user_id,
        job_role_id=jp.job_role_id,
        role=jp.title or "Software Engineer",
        difficulty=template.difficulty if template else "Medium",
        interview_type=template.interview_type if template else "Technical",
        status="pending",
    )
    db.add(session)
    db.commit()
    db.refresh(session)

    # Update application stage
    old_status = app.status
    app.status = "interview_scheduled"
    history = ApplicationHistory(
        application_id=app_id,
        from_stage=old_status,
        to_stage="interview_scheduled",
        reason=f"Interview assigned (session #{session.id})",
        actor_id=recruiter.id,
        actor_role="recruiter",
    )
    db.add(history)
    db.commit()

    log_activity(db, recruiter.id, "interview_assigned", "application", app_id,
                 {"session_id": session.id, "template_id": template.id if template else None})

    user = db.query(User).filter(User.id == app.user_id).first()
    create_notification(db, recruiter.id, "Interview Assigned",
                       f"Interview assigned for {user.name if user else 'candidate'} - {jp.title or 'a position'}")

    return {"message": "Interview assigned", "session_id": session.id}


@router.post("/applications/{app_id}/assign-coding")
def assign_coding(
    app_id: int,
    body: dict = None,
    recruiter: User = Depends(verify_recruiter),
    db: Session = Depends(get_db)
):
    app = db.query(Application).filter(Application.id == app_id).first()
    if not app:
        raise HTTPException(status_code=404, detail="Application not found")

    jp = db.query(RecruiterJobPost).filter(
        RecruiterJobPost.id == app.job_post_id,
        RecruiterJobPost.recruiter_id == recruiter.id,
    ).first()
    if not jp:
        raise HTTPException(status_code=403, detail="Access denied")

    # Get template if specified
    template = None
    challenge_id = None
    if body and body.get("template_id"):
        template = db.query(CodingTemplate).filter(
            CodingTemplate.id == body["template_id"],
            CodingTemplate.recruiter_id == recruiter.id,
        ).first()
        if template and template.challenge_ids:
            challenge_id = template.challenge_ids[0]

    # Create coding session
    coding_session = CodingSession(
        user_id=app.user_id,
        interview_session_id=None,
        challenge_id=challenge_id,
        status="in_progress",
    )
    db.add(coding_session)
    db.commit()
    db.refresh(coding_session)

    # Update application stage and link session
    old_status = app.status
    app.status = "coding_round"
    app.coding_session_id = coding_session.id
    history = ApplicationHistory(
        application_id=app_id,
        from_stage=old_status,
        to_stage="coding_round",
        reason=f"Coding assigned (session #{coding_session.id})",
        actor_id=recruiter.id,
        actor_role="recruiter",
    )
    db.add(history)
    db.commit()

    log_activity(db, recruiter.id, "coding_assigned", "application", app_id,
                 {"coding_session_id": coding_session.id, "template_id": template.id if template else None})

    user = db.query(User).filter(User.id == app.user_id).first()
    create_notification(db, recruiter.id, "Coding Assigned",
                       f"Coding assessment assigned for {user.name if user else 'candidate'} - {jp.title or 'a position'}")

    return {"message": "Coding assigned", "coding_session_id": coding_session.id}


# ═══════════════════════════════════════════════════════════════════════════════
# COMPARISON
# ═══════════════════════════════════════════════════════════════════════════════

@router.post("/compare", response_model=CandidateComparison)
def compare_candidates(
    body: dict,
    recruiter: User = Depends(verify_recruiter),
    db: Session = Depends(get_db)
):
    application_ids = body.get("application_ids", [])
    if len(application_ids) < 2:
        raise HTTPException(status_code=400, detail="At least 2 application IDs required")
    if len(application_ids) > 5:
        raise HTTPException(status_code=400, detail="Maximum 5 candidates for comparison")

    candidates = []
    for app_id in application_ids:
        app = db.query(Application).filter(Application.id == app_id).first()
        if not app:
            continue

        jp = db.query(RecruiterJobPost).filter(
            RecruiterJobPost.id == app.job_post_id,
            RecruiterJobPost.recruiter_id == recruiter.id,
        ).first()
        if not jp:
            continue

        user = db.query(User).filter(User.id == app.user_id).first()
        scores = _get_candidate_scores(db, app.user_id, app.job_post_id)

        candidates.append({
            "application_id": app.id,
            "user_id": app.user_id,
            "name": user.name if user else "Unknown",
            "email": user.email if user else "",
            "status": app.status,
            "ats_score": scores.get("ats_score"),
            "resume_match": scores.get("resume_match"),
            "interview_score": scores.get("interview_score"),
            "coding_score": scores.get("coding_score"),
            "career_readiness": scores.get("career_readiness"),
        })

    # Rankings
    rankings = {}
    for metric in ["ats_score", "resume_match", "interview_score", "coding_score", "career_readiness"]:
        scored = [(c["name"], c.get(metric) or 0) for c in candidates if c.get(metric) is not None]
        scored.sort(key=lambda x: x[1], reverse=True)
        rankings[metric] = [s[0] for s in scored]

    # Overall ranking (average of available scores)
    for c in candidates:
        available = [v for v in [c.get("ats_score"), c.get("resume_match"),
                                  c.get("interview_score"), c.get("coding_score"),
                                  c.get("career_readiness")] if v is not None]
        c["overall_avg"] = sum(available) / len(available) if available else 0

    candidates.sort(key=lambda c: c.get("overall_avg", 0), reverse=True)
    rankings["overall"] = [c["name"] for c in candidates]

    return CandidateComparison(candidates=candidates, rankings=rankings)


# ═══════════════════════════════════════════════════════════════════════════════
# NOTIFICATIONS
# ═══════════════════════════════════════════════════════════════════════════════

@router.get("/notifications", response_model=List[RecruiterNotificationResponse])
def get_notifications(
    unread_only: bool = False,
    recruiter: User = Depends(verify_recruiter),
    db: Session = Depends(get_db)
):
    query = db.query(Notification).filter(Notification.user_id == recruiter.id)
    if unread_only:
        query = query.filter(Notification.is_read == False)
    notifs = query.order_by(Notification.created_at.desc()).limit(50).all()
    return notifs


@router.patch("/notifications/{notif_id}/read")
def mark_notification_read(
    notif_id: int,
    recruiter: User = Depends(verify_recruiter),
    db: Session = Depends(get_db)
):
    notif = db.query(Notification).filter(
        Notification.id == notif_id,
        Notification.user_id == recruiter.id,
    ).first()
    if not notif:
        raise HTTPException(status_code=404, detail="Notification not found")

    notif.is_read = True
    db.commit()
    return {"message": "Marked as read"}


# ═══════════════════════════════════════════════════════════════════════════════
# ACTIVITY LOG
# ═══════════════════════════════════════════════════════════════════════════════

@router.get("/activity", response_model=List[RecruiterActivityResponse])
def get_activity(
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=100),
    recruiter: User = Depends(verify_recruiter),
    db: Session = Depends(get_db)
):
    activities = db.query(RecruiterActivity).filter(
        RecruiterActivity.recruiter_id == recruiter.id
    ).order_by(RecruiterActivity.created_at.desc()).offset(
        (page - 1) * per_page
    ).limit(per_page).all()

    return [
        RecruiterActivityResponse(
            id=a.id, action=a.action, target_type=a.target_type,
            target_id=a.target_id, details=a.details, created_at=a.created_at,
        )
        for a in activities
    ]


# ═══════════════════════════════════════════════════════════════════════════════
# COMPANIES
# ═══════════════════════════════════════════════════════════════════════════════

from app.models.recruiter import Company, ApplicationNote, CandidateAssignment
from app.schemas.recruiter_v2 import (
    CompanyCreate, CompanyResponse,
    ApplicationNoteCreate, ApplicationNoteResponse,
    AssignmentCreate, AssignmentResponse,
    RecruiterDecision, FinalEvaluation,
)


@router.get("/companies", response_model=List[CompanyResponse])
def list_companies(
    recruiter: User = Depends(verify_recruiter),
    db: Session = Depends(get_db)
):
    companies = db.query(Company).filter(
        Company.recruiter_id == recruiter.id
    ).order_by(Company.created_at.desc()).all()
    return companies


@router.post("/companies", response_model=CompanyResponse)
def create_company(
    company_in: CompanyCreate,
    recruiter: User = Depends(verify_recruiter),
    db: Session = Depends(get_db)
):
    company = Company(
        recruiter_id=recruiter.id,
        name=company_in.name,
        description=company_in.description,
        website=company_in.website,
        logo_url=company_in.logo_url,
        industry=company_in.industry,
        size=company_in.size,
        location=company_in.location,
    )
    db.add(company)
    db.commit()
    db.refresh(company)
    return company


@router.get("/companies/{company_id}", response_model=CompanyResponse)
def get_company(
    company_id: int,
    recruiter: User = Depends(verify_recruiter),
    db: Session = Depends(get_db)
):
    company = db.query(Company).filter(
        Company.id == company_id,
        Company.recruiter_id == recruiter.id,
    ).first()
    if not company:
        raise HTTPException(status_code=404, detail="Company not found")
    return company


@router.delete("/companies/{company_id}")
def delete_company(
    company_id: int,
    recruiter: User = Depends(verify_recruiter),
    db: Session = Depends(get_db)
):
    company = db.query(Company).filter(
        Company.id == company_id,
        Company.recruiter_id == recruiter.id,
    ).first()
    if not company:
        raise HTTPException(status_code=404, detail="Company not found")
    db.delete(company)
    db.commit()
    return {"message": "Company deleted"}


# ═══════════════════════════════════════════════════════════════════════════════
# APPLICATION NOTES
# ═══════════════════════════════════════════════════════════════════════════════

@router.get("/applications/{app_id}/notes", response_model=List[ApplicationNoteResponse])
def list_notes(
    app_id: int,
    recruiter: User = Depends(verify_recruiter),
    db: Session = Depends(get_db)
):
    app = db.query(Application).filter(Application.id == app_id).first()
    if not app:
        raise HTTPException(status_code=404, detail="Application not found")
    jp = db.query(RecruiterJobPost).filter(
        RecruiterJobPost.id == app.job_post_id,
        RecruiterJobPost.recruiter_id == recruiter.id,
    ).first()
    if not jp:
        raise HTTPException(status_code=403, detail="Access denied")

    notes = db.query(ApplicationNote).filter(
        ApplicationNote.application_id == app_id
    ).order_by(ApplicationNote.created_at.desc()).all()

    result = []
    for n in notes:
        user = db.query(User).filter(User.id == n.recruiter_id).first()
        result.append(ApplicationNoteResponse(
            id=n.id,
            application_id=n.application_id,
            recruiter_id=n.recruiter_id,
            recruiter_name=user.name if user else None,
            note=n.note,
            is_internal=n.is_internal,
            created_at=n.created_at,
        ))
    return result


@router.post("/applications/{app_id}/notes", response_model=ApplicationNoteResponse)
def add_note(
    app_id: int,
    note_in: ApplicationNoteCreate,
    recruiter: User = Depends(verify_recruiter),
    db: Session = Depends(get_db)
):
    app = db.query(Application).filter(Application.id == app_id).first()
    if not app:
        raise HTTPException(status_code=404, detail="Application not found")
    jp = db.query(RecruiterJobPost).filter(
        RecruiterJobPost.id == app.job_post_id,
        RecruiterJobPost.recruiter_id == recruiter.id,
    ).first()
    if not jp:
        raise HTTPException(status_code=403, detail="Access denied")

    note = ApplicationNote(
        application_id=app_id,
        recruiter_id=recruiter.id,
        note=note_in.note,
        is_internal=note_in.is_internal,
    )
    db.add(note)
    db.commit()
    db.refresh(note)

    return ApplicationNoteResponse(
        id=note.id,
        application_id=note.application_id,
        recruiter_id=note.recruiter_id,
        recruiter_name=recruiter.name,
        note=note.note,
        is_internal=note.is_internal,
        created_at=note.created_at,
    )


# ═══════════════════════════════════════════════════════════════════════════════
# ASSIGNMENTS (Interview/Coding from Recruiter to Candidate)
# ═══════════════════════════════════════════════════════════════════════════════

@router.post("/applications/{app_id}/assign", response_model=AssignmentResponse)
def create_assignment(
    app_id: int,
    assign_in: AssignmentCreate,
    recruiter: User = Depends(verify_recruiter),
    db: Session = Depends(get_db)
):
    app = db.query(Application).filter(Application.id == app_id).first()
    if not app:
        raise HTTPException(status_code=404, detail="Application not found")
    jp = db.query(RecruiterJobPost).filter(
        RecruiterJobPost.id == app.job_post_id,
        RecruiterJobPost.recruiter_id == recruiter.id,
    ).first()
    if not jp:
        raise HTTPException(status_code=403, detail="Access denied")

    assignment = CandidateAssignment(
        application_id=app_id,
        assignment_type=assign_in.assignment_type,
        template_id=assign_in.template_id,
        assigned_by=recruiter.id,
        assigned_to=app.user_id,
        status="pending",
        due_date=assign_in.due_date,
        notes=assign_in.notes,
    )
    db.add(assignment)

    # Update application status
    if assign_in.assignment_type == "interview":
        old_status = app.status
        app.status = "interview_scheduled"
        history = ApplicationHistory(
            application_id=app.id,
            from_stage=old_status,
            to_stage="interview_scheduled",
            reason="Interview assigned by recruiter",
            actor_id=recruiter.id,
            actor_role="recruiter",
        )
        db.add(history)
    elif assign_in.assignment_type == "coding":
        old_status = app.status
        app.status = "coding_round"
        history = ApplicationHistory(
            application_id=app.id,
            from_stage=old_status,
            to_stage="coding_round",
            reason="Coding assessment assigned by recruiter",
            actor_id=recruiter.id,
            actor_role="recruiter",
        )
        db.add(history)

    db.commit()
    db.refresh(assignment)

    # Notify candidate
    try:
        notif = Notification(
            user_id=app.user_id,
            title=f"New {assign_in.assignment_type.title()} Assignment",
            message=f"You have been assigned a {assign_in.assignment_type} assessment. Complete it by {assign_in.due_date.strftime('%B %d') if assign_in.due_date else 'no deadline'}.",
            type="info",
        )
        db.add(notif)
        db.commit()
    except Exception:
        pass

    log_activity(db, recruiter.id, "assignment_created", "application", app_id,
                 {"type": assign_in.assignment_type})

    return assignment


@router.get("/applications/{app_id}/assignments", response_model=List[AssignmentResponse])
def list_app_assignments(
    app_id: int,
    recruiter: User = Depends(verify_recruiter),
    db: Session = Depends(get_db)
):
    app = db.query(Application).filter(Application.id == app_id).first()
    if not app:
        raise HTTPException(status_code=404, detail="Application not found")

    assignments = db.query(CandidateAssignment).filter(
        CandidateAssignment.application_id == app_id
    ).order_by(CandidateAssignment.created_at.desc()).all()
    return assignments


# ═══════════════════════════════════════════════════════════════════════════════
# RECRUITER DECISION
# ═══════════════════════════════════════════════════════════════════════════════

@router.post("/applications/{app_id}/decision")
def make_decision(
    app_id: int,
    decision_in: RecruiterDecision,
    recruiter: User = Depends(verify_recruiter),
    db: Session = Depends(get_db)
):
    """Recruiter makes a hiring decision on an application."""
    app = db.query(Application).filter(Application.id == app_id).first()
    if not app:
        raise HTTPException(status_code=404, detail="Application not found")
    jp = db.query(RecruiterJobPost).filter(
        RecruiterJobPost.id == app.job_post_id,
        RecruiterJobPost.recruiter_id == recruiter.id,
    ).first()
    if not jp:
        raise HTTPException(status_code=403, detail="Access denied")

    valid_decisions = ["shortlisted", "rejected", "hold", "offer_released", "hired"]
    if decision_in.decision not in valid_decisions:
        raise HTTPException(status_code=400, detail=f"Decision must be one of: {valid_decisions}")

    old_status = app.status
    app.status = decision_in.decision
    app.decision = decision_in.decision
    app.decision_at = datetime.now(timezone.utc)
    app.decision_by = recruiter.id
    app.decision_reason = decision_in.reason

    history = ApplicationHistory(
        application_id=app.id,
        from_stage=old_status,
        to_stage=decision_in.decision,
        reason=decision_in.reason,
        actor_id=recruiter.id,
        actor_role="recruiter",
    )
    db.add(history)

    # Also create shortlist entry
    shortlist = Shortlist(
        application_id=app.id,
        recruiter_id=recruiter.id,
        action=decision_in.decision,
        reason=decision_in.reason,
        comments=decision_in.notes,
    )
    db.add(shortlist)
    db.commit()

    # Notify candidate
    try:
        notif = Notification(
            user_id=app.user_id,
            title=f"Application {decision_in.decision.replace('_', ' ').title()}",
            message=f"Your application for {jp.title or 'a position'} has been {decision_in.decision.replace('_', ' ')}.",
            type="success" if decision_in.decision in ("shortlisted", "hired") else "warning" if decision_in.decision == "hold" else "info",
        )
        db.add(notif)
        db.commit()
    except Exception:
        pass

    log_activity(db, recruiter.id, f"decision_{decision_in.decision}", "application", app_id,
                 {"decision": decision_in.decision, "reason": decision_in.reason})

    return {"message": f"Decision recorded: {decision_in.decision}"}


@router.post("/applications/{app_id}/evaluate")
def final_evaluation(
    app_id: int,
    eval_in: FinalEvaluation,
    recruiter: User = Depends(verify_recruiter),
    db: Session = Depends(get_db)
):
    """Store final AI evaluation for an application."""
    app = db.query(Application).filter(Application.id == app_id).first()
    if not app:
        raise HTTPException(status_code=404, detail="Application not found")
    jp = db.query(RecruiterJobPost).filter(
        RecruiterJobPost.id == app.job_post_id,
        RecruiterJobPost.recruiter_id == recruiter.id,
    ).first()
    if not jp:
        raise HTTPException(status_code=403, detail="Access denied")

    app.final_interview_score = eval_in.final_interview_score
    app.final_coding_score = eval_in.final_coding_score
    app.final_composite_score = eval_in.final_composite_score
    app.hiring_recommendation = eval_in.hiring_recommendation
    app.strengths = eval_in.strengths
    app.weaknesses = eval_in.weaknesses
    db.commit()

    log_activity(db, recruiter.id, "final_evaluation", "application", app_id,
                 {"composite_score": eval_in.final_composite_score})

    return {"message": "Final evaluation saved"}
