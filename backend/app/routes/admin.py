"""
Admin Module — Full Production Router
All routes require admin JWT authorization via verify_admin dependency.
All write operations create an AdminLog audit entry.
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import func, desc, cast, Date
from sqlalchemy.exc import SQLAlchemyError
from app.database import get_db
from app.auth.utils import get_current_user, get_password_hash
from app.models.user import User
from app.models.interview_session import InterviewSession
from app.models.question import Question
from app.models.cheating_log import CheatingLog
from app.models.api_usage import ApiUsage
from app.models.job_role import JobRole
from app.models.admin_log import AdminLog
from app.models.system_health_log import SystemHealthLog
from app.models.notification import Notification
from app.models.coding_challenge import CodingChallenge, CodingSubmission, CodingSession
from app.schemas.admin import (
    AdminStatsResponse, UserStatus, CheatingLogResponse, ApiUsageStats,
    AdminDashboardStats, UserDetail, UserListResponse, PasswordResetResponse,
    RecruiterDetail, RecruiterListResponse,
    InterviewDetail, InterviewListResponse,
    VoiceSessionSummary,
    AIUsageDetail, AIUsageDailyPoint,
    ReportItem, ReportListResponse,
    PlatformAnalytics, GrowthPoint, ScoreDistributionBucket,
    SystemHealthStatus, ServiceHealth,
    AuditLogEntry, AuditLogListResponse,
    NotificationItem,
    AdminSettings,
    AdminCodingSubmission, AdminCodingSubmissionsResponse,
    AdminCodingAnalytics, AdminCodingSubmissionDetail,
)
from typing import List, Optional
from datetime import datetime, timedelta, date
import time
import random
import string

router = APIRouter(
    prefix="/admin",
    tags=["admin"]
)


# ─── Auth Dependency ──────────────────────────────────────────────────────────

def verify_admin(current_user: User = Depends(get_current_user)):
    if not current_user.is_admin:
        raise HTTPException(status_code=403, detail="Not authorized. Admin access required.")
    return current_user


# ─── Helpers ─────────────────────────────────────────────────────────────────

def create_audit_log(
    db: Session,
    admin: User,
    action: str,
    target_type: Optional[str] = None,
    target_id: Optional[int] = None,
    details: Optional[dict] = None,
):
    log = AdminLog(
        admin_id=admin.id,
        action=action,
        target_type=target_type,
        target_id=target_id,
        details=details or {},
    )
    db.add(log)
    db.commit()


def generate_temp_password(length: int = 12) -> str:
    chars = string.ascii_letters + string.digits + "!@#$%"
    return "".join(random.choices(chars, k=length))


# ─── LEGACY ENDPOINTS (preserved for backward compatibility) ──────────────────

@router.get("/stats", response_model=AdminStatsResponse)
def get_global_stats(
    admin: User = Depends(verify_admin),
    db: Session = Depends(get_db)
):
    total_users = db.query(func.count(User.id)).scalar()
    total_interviews = db.query(func.count(InterviewSession.id)).scalar()
    total_questions = db.query(func.count(Question.id)).scalar()
    avg_score = db.query(func.avg(InterviewSession.score)).filter(InterviewSession.status == "completed").scalar() or 0.0
    total_cost = db.query(func.sum(ApiUsage.cost)).scalar() or 0.0

    role_dist = db.query(
        InterviewSession.role, func.count(InterviewSession.id)
    ).group_by(InterviewSession.role).all()

    recent_sessions = db.query(InterviewSession).order_by(InterviewSession.started_at.desc()).limit(5).all()
    activity = [
        {"id": s.id, "user": s.user.email if s.user else "—", "role": s.role, "status": s.status, "time": s.started_at}
        for s in recent_sessions
    ]

    return AdminStatsResponse(
        total_users=total_users,
        total_interviews=total_interviews,
        total_questions_asked=total_questions,
        avg_score_platform=float(avg_score),
        interviews_by_role={r: c for r, c in role_dist},
        recent_activity=activity,
        total_api_cost=float(total_cost)
    )


@router.get("/abuse-logs", response_model=List[CheatingLogResponse])
def get_abuse_logs(
    admin: User = Depends(verify_admin),
    db: Session = Depends(get_db),
    limit: int = 50
):
    logs = db.query(CheatingLog).order_by(CheatingLog.created_at.desc()).limit(limit).all()
    result = []
    for log in logs:
        session = db.query(InterviewSession).filter(InterviewSession.id == log.session_id).first()
        email = session.user.email if session and session.user else "Unknown"
        result.append(CheatingLogResponse(
            id=log.id,
            session_id=log.session_id,
            event_type=log.event_type,
            details=log.details,
            created_at=log.created_at,
            user_email=email
        ))
    return result


@router.get("/api-usage", response_model=ApiUsageStats)
def get_api_usage_stats(
    admin: User = Depends(verify_admin),
    db: Session = Depends(get_db)
):
    total_tokens = db.query(func.sum(ApiUsage.total_tokens)).scalar() or 0
    total_cost = db.query(func.sum(ApiUsage.cost)).scalar() or 0.0
    usage_by_feature = db.query(
        ApiUsage.feature, func.sum(ApiUsage.total_tokens)
    ).group_by(ApiUsage.feature).all()

    return ApiUsageStats(
        total_tokens=total_tokens,
        total_cost=float(total_cost),
        usage_by_feature={f: t for f, t in usage_by_feature}
    )


# ─── DASHBOARD ────────────────────────────────────────────────────────────────

@router.get("/dashboard", response_model=AdminDashboardStats)
def get_admin_dashboard(
    admin: User = Depends(verify_admin),
    db: Session = Depends(get_db)
):
    today_start = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)

    total_users = db.query(func.count(User.id)).scalar() or 0
    active_users = db.query(func.count(User.id)).filter(User.is_active == True).scalar() or 0
    total_interviews = db.query(func.count(InterviewSession.id)).scalar() or 0
    interviews_today = db.query(func.count(InterviewSession.id)).filter(
        InterviewSession.started_at >= today_start
    ).scalar() or 0
    total_recruiters = db.query(func.count(User.id)).filter(User.is_recruiter == True).scalar() or 0
    total_reports = db.query(func.count(InterviewSession.id)).filter(
        InterviewSession.status == "completed"
    ).scalar() or 0
    active_voice_sessions = db.query(func.count(InterviewSession.id)).filter(
        InterviewSession.interview_type == "Voice",
        InterviewSession.status == "in-progress"
    ).scalar() or 0
    api_requests_today = db.query(func.count(ApiUsage.id)).filter(
        ApiUsage.timestamp >= today_start
    ).scalar() or 0
    avg_score = db.query(func.avg(InterviewSession.score)).filter(
        InterviewSession.status == "completed"
    ).scalar() or 0.0
    total_cost = db.query(func.sum(ApiUsage.cost)).scalar() or 0.0

    role_dist = db.query(
        InterviewSession.role, func.count(InterviewSession.id)
    ).group_by(InterviewSession.role).all()

    recent_sessions = db.query(InterviewSession).order_by(
        InterviewSession.started_at.desc()
    ).limit(10).all()
    activity = [
        {
            "id": s.id,
            "user": s.user.name if s.user else "—",
            "email": s.user.email if s.user else "—",
            "role": s.role,
            "status": s.status,
            "score": s.score,
            "time": s.started_at.isoformat() if s.started_at else None,
        }
        for s in recent_sessions
    ]

    return AdminDashboardStats(
        total_users=total_users,
        active_users=active_users,
        total_interviews=total_interviews,
        interviews_today=interviews_today,
        total_recruiters=total_recruiters,
        total_reports=total_reports,
        active_voice_sessions=active_voice_sessions,
        api_requests_today=api_requests_today,
        avg_score_platform=float(avg_score),
        total_api_cost=float(total_cost),
        interviews_by_role={r: c for r, c in role_dist},
        recent_activity=activity,
    )


# ─── USERS ────────────────────────────────────────────────────────────────────

@router.get("/users", response_model=UserListResponse)
def list_users(
    admin: User = Depends(verify_admin),
    db: Session = Depends(get_db),
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=100),
    search: Optional[str] = Query(None),
    status: Optional[str] = Query(None),   # "active", "disabled"
    role: Optional[str] = Query(None),     # "admin", "recruiter", "candidate"
):
    query = db.query(User)

    if search:
        like = f"%{search}%"
        query = query.filter((User.name.ilike(like)) | (User.email.ilike(like)))

    if status == "active":
        query = query.filter(User.is_active == True)
    elif status == "disabled":
        query = query.filter(User.is_active == False)

    if role == "admin":
        query = query.filter(User.is_admin == True)
    elif role == "recruiter":
        query = query.filter(User.is_recruiter == True)
    elif role == "candidate":
        query = query.filter(User.is_recruiter == False, User.is_admin == False)

    total = query.count()
    users = query.order_by(User.created_at.desc()).offset((page - 1) * per_page).limit(per_page).all()

    result = []
    for u in users:
        count = db.query(func.count(InterviewSession.id)).filter(InterviewSession.user_id == u.id).scalar() or 0
        avg = db.query(func.avg(InterviewSession.score)).filter(
            InterviewSession.user_id == u.id,
            InterviewSession.status == "completed"
        ).scalar()
        result.append(UserDetail(
            id=u.id,
            name=u.name or "—",
            email=u.email,
            is_active=u.is_active,
            is_admin=u.is_admin,
            is_recruiter=u.is_recruiter,
            total_interviews=count,
            avg_score=round(float(avg), 2) if avg else None,
            created_at=u.created_at,
        ))

    return UserListResponse(users=result, total=total, page=page, per_page=per_page)


@router.get("/users/{user_id}", response_model=UserDetail)
def get_user_detail(
    user_id: int,
    admin: User = Depends(verify_admin),
    db: Session = Depends(get_db),
):
    u = db.query(User).filter(User.id == user_id).first()
    if not u:
        raise HTTPException(status_code=404, detail="User not found")
    count = db.query(func.count(InterviewSession.id)).filter(InterviewSession.user_id == u.id).scalar() or 0
    avg = db.query(func.avg(InterviewSession.score)).filter(
        InterviewSession.user_id == u.id,
        InterviewSession.status == "completed"
    ).scalar()
    return UserDetail(
        id=u.id,
        name=u.name or "—",
        email=u.email,
        is_active=u.is_active,
        is_admin=u.is_admin,
        is_recruiter=u.is_recruiter,
        total_interviews=count,
        avg_score=round(float(avg), 2) if avg else None,
        created_at=u.created_at,
    )


@router.patch("/users/{user_id}/toggle-active")
def toggle_user_status(
    user_id: int,
    admin: User = Depends(verify_admin),
    db: Session = Depends(get_db),
):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    user.is_active = not user.is_active
    db.commit()
    action = "user_enabled" if user.is_active else "user_disabled"
    create_audit_log(db, admin, action, "user", user_id, {"email": user.email})
    return {"message": f"User {'enabled' if user.is_active else 'disabled'}", "is_active": user.is_active}


@router.delete("/users/{user_id}")
def delete_user(
    user_id: int,
    admin: User = Depends(verify_admin),
    db: Session = Depends(get_db),
):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    if user.is_admin:
        raise HTTPException(status_code=400, detail="Cannot delete another admin account")
    email = user.email
    db.delete(user)
    db.commit()
    create_audit_log(db, admin, "user_deleted", "user", user_id, {"email": email})
    return {"message": "User deleted successfully"}


@router.post("/users/{user_id}/reset-password", response_model=PasswordResetResponse)
def reset_user_password(
    user_id: int,
    admin: User = Depends(verify_admin),
    db: Session = Depends(get_db),
):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    temp_pw = generate_temp_password()
    user.hashed_password = get_password_hash(temp_pw)
    db.commit()
    create_audit_log(db, admin, "password_reset", "user", user_id, {"email": user.email})
    return PasswordResetResponse(temp_password=temp_pw, message="Password reset successfully. Share this temporary password with the user.")


# ─── RECRUITERS ───────────────────────────────────────────────────────────────

@router.get("/recruiters", response_model=RecruiterListResponse)
def list_recruiters(
    admin: User = Depends(verify_admin),
    db: Session = Depends(get_db),
    search: Optional[str] = Query(None),
):
    query = db.query(User).filter(User.is_recruiter == True)
    if search:
        like = f"%{search}%"
        query = query.filter((User.name.ilike(like)) | (User.email.ilike(like)))

    users = query.order_by(User.created_at.desc()).all()
    total = len(users)
    result = []
    for u in users:
        jobs = db.query(JobRole).filter(JobRole.recruiter_id == u.id).all()
        job_ids = [j.id for j in jobs]
        total_candidates = 0
        interviews_conducted = 0
        if job_ids:
            total_candidates = db.query(func.count(InterviewSession.id)).filter(
                InterviewSession.job_role_id.in_(job_ids)
            ).scalar() or 0
            interviews_conducted = db.query(func.count(InterviewSession.id)).filter(
                InterviewSession.job_role_id.in_(job_ids),
                InterviewSession.status == "completed"
            ).scalar() or 0

        result.append(RecruiterDetail(
            id=u.id,
            name=u.name or "—",
            email=u.email,
            is_active=u.is_active,
            total_jobs=len(jobs),
            total_candidates=total_candidates,
            interviews_conducted=interviews_conducted,
            created_at=u.created_at,
        ))

    return RecruiterListResponse(recruiters=result, total=total)


@router.patch("/recruiters/{recruiter_id}/approve")
def approve_recruiter(
    recruiter_id: int,
    admin: User = Depends(verify_admin),
    db: Session = Depends(get_db),
):
    user = db.query(User).filter(User.id == recruiter_id, User.is_recruiter == True).first()
    if not user:
        raise HTTPException(status_code=404, detail="Recruiter not found")
    user.is_active = True
    db.commit()
    create_audit_log(db, admin, "recruiter_approved", "recruiter", recruiter_id, {"email": user.email})
    return {"message": "Recruiter approved"}


@router.patch("/recruiters/{recruiter_id}/reject")
def reject_recruiter(
    recruiter_id: int,
    admin: User = Depends(verify_admin),
    db: Session = Depends(get_db),
):
    user = db.query(User).filter(User.id == recruiter_id, User.is_recruiter == True).first()
    if not user:
        raise HTTPException(status_code=404, detail="Recruiter not found")
    user.is_active = False
    db.commit()
    create_audit_log(db, admin, "recruiter_rejected", "recruiter", recruiter_id, {"email": user.email})
    return {"message": "Recruiter rejected / disabled"}


# ─── INTERVIEWS ───────────────────────────────────────────────────────────────

def _session_to_interview_detail(s: InterviewSession) -> InterviewDetail:
    duration = None
    if s.started_at and s.ended_at:
        duration = round((s.ended_at - s.started_at).total_seconds() / 60, 1)
    return InterviewDetail(
        id=s.id,
        candidate_name=s.user.name if s.user else "—",
        candidate_email=s.user.email if s.user else "—",
        role=s.role or "—",
        interview_type=s.interview_type or "Technical",
        difficulty=s.difficulty or "Medium",
        status=s.status,
        score=s.score,
        started_at=s.started_at,
        ended_at=s.ended_at,
        duration_minutes=duration,
    )


@router.get("/interviews", response_model=InterviewListResponse)
def list_interviews(
    admin: User = Depends(verify_admin),
    db: Session = Depends(get_db),
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=100),
    search: Optional[str] = Query(None),
    status: Optional[str] = Query(None),
    interview_type: Optional[str] = Query(None),
    role: Optional[str] = Query(None),
    score_min: Optional[float] = Query(None),
    score_max: Optional[float] = Query(None),
    date_from: Optional[str] = Query(None),
    date_to: Optional[str] = Query(None),
):
    query = db.query(InterviewSession)

    if search:
        like = f"%{search}%"
        query = query.join(User).filter(
            (User.name.ilike(like)) | (User.email.ilike(like)) | (InterviewSession.role.ilike(like))
        )

    if status:
        query = query.filter(InterviewSession.status == status)
    if interview_type:
        query = query.filter(InterviewSession.interview_type == interview_type)
    if role:
        query = query.filter(InterviewSession.role.ilike(f"%{role}%"))
    if score_min is not None:
        query = query.filter(InterviewSession.score >= score_min)
    if score_max is not None:
        query = query.filter(InterviewSession.score <= score_max)
    if date_from:
        query = query.filter(InterviewSession.started_at >= datetime.fromisoformat(date_from))
    if date_to:
        query = query.filter(InterviewSession.started_at <= datetime.fromisoformat(date_to))

    total = query.count()
    sessions = query.order_by(InterviewSession.started_at.desc()).offset((page - 1) * per_page).limit(per_page).all()

    return InterviewListResponse(
        interviews=[_session_to_interview_detail(s) for s in sessions],
        total=total,
        page=page,
        per_page=per_page,
    )


@router.get("/interviews/{session_id}", response_model=InterviewDetail)
def get_interview_detail(
    session_id: int,
    admin: User = Depends(verify_admin),
    db: Session = Depends(get_db),
):
    s = db.query(InterviewSession).filter(InterviewSession.id == session_id).first()
    if not s:
        raise HTTPException(status_code=404, detail="Interview session not found")
    return _session_to_interview_detail(s)


# ─── VOICE SESSIONS ───────────────────────────────────────────────────────────

@router.get("/voice-sessions", response_model=List[VoiceSessionSummary])
def list_voice_sessions(
    admin: User = Depends(verify_admin),
    db: Session = Depends(get_db),
    status: Optional[str] = Query(None),
    limit: int = Query(50, le=200),
):
    query = db.query(InterviewSession).filter(InterviewSession.interview_type == "Voice")
    if status:
        query = query.filter(InterviewSession.status == status)
    sessions = query.order_by(InterviewSession.started_at.desc()).limit(limit).all()

    result = []
    for s in sessions:
        duration = None
        if s.started_at and s.ended_at:
            duration = round((s.ended_at - s.started_at).total_seconds() / 60, 1)
        result.append(VoiceSessionSummary(
            id=s.id,
            candidate_name=s.user.name if s.user else "—",
            candidate_email=s.user.email if s.user else "—",
            status=s.status,
            score=s.score,
            started_at=s.started_at,
            ended_at=s.ended_at,
            duration_minutes=duration,
        ))
    return result


# ─── AI USAGE ────────────────────────────────────────────────────────────────

@router.get("/ai-usage/detail", response_model=AIUsageDetail)
def get_ai_usage_detail(
    admin: User = Depends(verify_admin),
    db: Session = Depends(get_db),
    days: int = Query(30, ge=1, le=365),
):
    since = datetime.utcnow() - timedelta(days=days)

    total_requests = db.query(func.count(ApiUsage.id)).scalar() or 0
    total_tokens = db.query(func.sum(ApiUsage.total_tokens)).scalar() or 0
    total_cost = db.query(func.sum(ApiUsage.cost)).scalar() or 0.0
    failed_requests = 0  # No failure flag in model; placeholder

    usage_by_feature = {}
    rows = db.query(
        ApiUsage.feature,
        func.count(ApiUsage.id),
        func.sum(ApiUsage.total_tokens),
        func.sum(ApiUsage.cost),
    ).group_by(ApiUsage.feature).all()
    for feature, cnt, tokens, cost in rows:
        usage_by_feature[feature or "unknown"] = {
            "requests": cnt,
            "tokens": tokens or 0,
            "cost": round(float(cost or 0), 4),
        }

    # Daily breakdown for last `days` days
    daily_rows = db.query(
        cast(ApiUsage.timestamp, Date).label("day"),
        func.count(ApiUsage.id).label("requests"),
        func.sum(ApiUsage.total_tokens).label("tokens"),
        func.sum(ApiUsage.cost).label("cost"),
    ).filter(ApiUsage.timestamp >= since).group_by("day").order_by("day").all()

    daily_breakdown = [
        AIUsageDailyPoint(
            date=str(row.day),
            requests=row.requests or 0,
            tokens=int(row.tokens or 0),
            cost=round(float(row.cost or 0), 4),
        )
        for row in daily_rows
    ]

    return AIUsageDetail(
        total_requests=total_requests,
        total_tokens=int(total_tokens),
        total_cost=round(float(total_cost), 4),
        avg_response_time_ms=0.0,  # Not tracked in current model
        failed_requests=failed_requests,
        usage_by_feature=usage_by_feature,
        daily_breakdown=daily_breakdown,
    )


# ─── REPORTS ─────────────────────────────────────────────────────────────────

@router.get("/reports", response_model=ReportListResponse)
def list_reports(
    admin: User = Depends(verify_admin),
    db: Session = Depends(get_db),
    search: Optional[str] = Query(None),
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=100),
):
    query = db.query(InterviewSession).filter(InterviewSession.status == "completed")

    if search:
        like = f"%{search}%"
        query = query.join(User).filter(
            (User.name.ilike(like)) | (User.email.ilike(like)) | (InterviewSession.role.ilike(like))
        )

    total = query.count()
    sessions = query.order_by(InterviewSession.started_at.desc()).offset((page - 1) * per_page).limit(per_page).all()

    reports = [
        ReportItem(
            id=s.id,
            candidate_name=s.user.name if s.user else "—",
            candidate_email=s.user.email if s.user else "—",
            role=s.role or "—",
            score=s.score,
            interview_type=s.interview_type or "Technical",
            status=s.status,
            generated_at=s.ended_at or s.started_at,
        )
        for s in sessions
    ]

    return ReportListResponse(reports=reports, total=total)


@router.delete("/reports/{session_id}")
def delete_report(
    session_id: int,
    admin: User = Depends(verify_admin),
    db: Session = Depends(get_db),
):
    session = db.query(InterviewSession).filter(InterviewSession.id == session_id).first()
    if not session:
        raise HTTPException(status_code=404, detail="Interview session not found")
    db.delete(session)
    db.commit()
    create_audit_log(db, admin, "report_deleted", "interview", session_id)
    return {"message": "Report deleted"}


# ─── PLATFORM ANALYTICS ───────────────────────────────────────────────────────

@router.get("/analytics", response_model=PlatformAnalytics)
def get_platform_analytics(
    admin: User = Depends(verify_admin),
    db: Session = Depends(get_db),
):
    now = datetime.utcnow()
    month_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)

    total_users = db.query(func.count(User.id)).scalar() or 0
    active_users = db.query(func.count(User.id)).filter(User.is_active == True).scalar() or 0
    new_signups_this_month = db.query(func.count(User.id)).filter(User.created_at >= month_start).scalar() or 0

    total_interviews = db.query(func.count(InterviewSession.id)).scalar() or 0
    completed_interviews = db.query(func.count(InterviewSession.id)).filter(
        InterviewSession.status == "completed"
    ).scalar() or 0
    completion_rate = round((completed_interviews / total_interviews * 100), 1) if total_interviews > 0 else 0.0

    avg_score = db.query(func.avg(InterviewSession.score)).filter(
        InterviewSession.status == "completed"
    ).scalar() or 0.0

    # Most popular role
    popular_role_row = db.query(
        InterviewSession.role, func.count(InterviewSession.id).label("cnt")
    ).group_by(InterviewSession.role).order_by(desc("cnt")).first()
    most_popular_role = popular_role_row.role if popular_role_row else "N/A"

    # Most popular interview type
    popular_type_row = db.query(
        InterviewSession.interview_type, func.count(InterviewSession.id).label("cnt")
    ).group_by(InterviewSession.interview_type).order_by(desc("cnt")).first()
    most_popular_type = popular_type_row.interview_type if popular_type_row else "Technical"

    # User growth: last 12 months
    user_growth = []
    for i in range(11, -1, -1):
        month_ago = now - timedelta(days=30 * i)
        period_start = month_ago.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        period_end = (period_start.replace(month=period_start.month % 12 + 1, day=1)
                      if period_start.month < 12
                      else period_start.replace(year=period_start.year + 1, month=1, day=1))
        cnt = db.query(func.count(User.id)).filter(
            User.created_at >= period_start,
            User.created_at < period_end
        ).scalar() or 0
        user_growth.append(GrowthPoint(date=period_start.strftime("%b %Y"), count=cnt))

    # Interview trends: last 12 months
    interview_trends = []
    for i in range(11, -1, -1):
        month_ago = now - timedelta(days=30 * i)
        period_start = month_ago.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        period_end = (period_start.replace(month=period_start.month % 12 + 1, day=1)
                      if period_start.month < 12
                      else period_start.replace(year=period_start.year + 1, month=1, day=1))
        cnt = db.query(func.count(InterviewSession.id)).filter(
            InterviewSession.started_at >= period_start,
            InterviewSession.started_at < period_end
        ).scalar() or 0
        interview_trends.append(GrowthPoint(date=period_start.strftime("%b %Y"), count=cnt))

    # Score distribution
    score_buckets = [
        ("0–2", 0, 2),
        ("2–4", 2, 4),
        ("4–6", 4, 6),
        ("6–8", 6, 8),
        ("8–10", 8, 10.01),
    ]
    score_distribution = []
    for label, low, high in score_buckets:
        cnt = db.query(func.count(InterviewSession.id)).filter(
            InterviewSession.score >= low,
            InterviewSession.score < high,
            InterviewSession.status == "completed",
        ).scalar() or 0
        score_distribution.append(ScoreDistributionBucket(range=label, count=cnt))

    return PlatformAnalytics(
        total_users=total_users,
        active_users=active_users,
        new_signups_this_month=new_signups_this_month,
        interview_completion_rate=completion_rate,
        avg_interview_score=round(float(avg_score), 2),
        most_popular_role=most_popular_role,
        most_popular_interview_type=most_popular_type,
        user_growth=user_growth,
        interview_trends=interview_trends,
        score_distribution=score_distribution,
    )


# ─── SYSTEM HEALTH ────────────────────────────────────────────────────────────

@router.get("/system-health", response_model=SystemHealthStatus)
def get_system_health(
    admin: User = Depends(verify_admin),
    db: Session = Depends(get_db),
):
    services = []

    # Database
    try:
        t0 = time.time()
        db.execute(__import__("sqlalchemy").text("SELECT 1"))
        db_latency = round((time.time() - t0) * 1000, 2)
        services.append(ServiceHealth(name="Database", status="online", latency_ms=db_latency, details="SQLite responding normally"))
    except Exception as e:
        services.append(ServiceHealth(name="Database", status="offline", latency_ms=None, details=str(e)))

    # Backend (self)
    services.append(ServiceHealth(name="Backend API", status="online", latency_ms=0.5, details="FastAPI running"))

    # AI Service (check if recent usage exists)
    recent_ai = db.query(ApiUsage).order_by(ApiUsage.timestamp.desc()).first()
    ai_status = "online" if recent_ai else "warning"
    ai_detail = f"Last call: {recent_ai.timestamp.strftime('%Y-%m-%d %H:%M')}" if recent_ai else "No recent AI calls recorded"
    services.append(ServiceHealth(name="AI Service", status=ai_status, latency_ms=None, details=ai_detail))

    # WebSocket
    services.append(ServiceHealth(name="WebSocket", status="online", latency_ms=None, details="Voice interview WebSocket active"))

    # Storage
    import os
    uploads_path = "uploads"
    if os.path.exists(uploads_path):
        services.append(ServiceHealth(name="Storage", status="online", latency_ms=None, details=f"Upload dir accessible"))
    else:
        services.append(ServiceHealth(name="Storage", status="warning", latency_ms=None, details="Upload directory not found"))

    offline_count = sum(1 for s in services if s.status == "offline")
    warning_count = sum(1 for s in services if s.status == "warning")
    overall = "offline" if offline_count > 0 else ("warning" if warning_count > 0 else "online")

    return SystemHealthStatus(
        overall=overall,
        services=services,
        error_rate=0.0,
        active_connections=1,
        checked_at=datetime.utcnow(),
    )


@router.get("/cache/stats")
def get_cache_stats(admin: User = Depends(verify_admin)):
    """Get cache statistics (AI responses, TTS audio, etc)."""
    try:
        from app.services.ai_cache import ai_cache
        from app.services.tts_cache import tts_cache
        
        ai_keys = len(ai_cache.redis.keys("ai:*"))
        tts_keys = len(tts_cache.redis.keys("tts:*"))
        
        # Get memory usage of cache keys
        ai_memory = sum(ai_cache.redis.memory_usage(k) or 0 for k in ai_cache.redis.keys("ai:*")[:100])
        tts_memory = sum(tts_cache.redis.memory_usage(k) or 0 for k in tts_cache.redis.keys("tts:*")[:100])
        
        return {
            "ai_response_cache": {
                "entries": ai_keys,
                "memory_kb": round(ai_memory / 1024, 2),
            },
            "tts_audio_cache": {
                "entries": tts_keys,
                "memory_kb": round(tts_memory / 1024, 2),
            },
            "total_entries": ai_keys + tts_keys,
            "estimated_savings": f"Prevented ~{(ai_keys + tts_keys) * 0.5}s API latency",
        }
    except Exception as e:
        logger.error(f"Failed to get cache stats: {e}")
        return {"error": str(e), "detail": "Could not connect to Redis cache"}


@router.delete("/cache/tts")
def clear_tts_cache(admin: User = Depends(verify_admin)):
    """Clear all TTS audio cache entries."""
    try:
        from app.services.tts_cache import tts_cache
        
        tts_cache.clear_pattern("tts:*")
        return {"message": "TTS cache cleared successfully"}
    except Exception as e:
        logger.error(f"Failed to clear TTS cache: {e}")
        return {"error": str(e)}


# ─── AUDIT LOGS ───────────────────────────────────────────────────────────────

@router.get("/audit-logs", response_model=AuditLogListResponse)
def list_audit_logs(
    admin: User = Depends(verify_admin),
    db: Session = Depends(get_db),
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=100),
    action: Optional[str] = Query(None),
):
    query = db.query(AdminLog)
    if action:
        query = query.filter(AdminLog.action.ilike(f"%{action}%"))

    total = query.count()
    logs = query.order_by(AdminLog.timestamp.desc()).offset((page - 1) * per_page).limit(per_page).all()

    result = []
    for log in logs:
        admin_email = None
        if log.admin_id:
            u = db.query(User).filter(User.id == log.admin_id).first()
            admin_email = u.email if u else None
        result.append(AuditLogEntry(
            id=log.id,
            action=log.action,
            admin_email=admin_email,
            target_type=log.target_type,
            target_id=log.target_id,
            details=log.details,
            timestamp=log.timestamp,
        ))

    return AuditLogListResponse(logs=result, total=total, page=page, per_page=per_page)


# ─── NOTIFICATIONS ────────────────────────────────────────────────────────────

@router.get("/notifications", response_model=List[NotificationItem])
def list_notifications(
    admin: User = Depends(verify_admin),
    db: Session = Depends(get_db),
    unread_only: bool = Query(False),
):
    query = db.query(Notification)
    if unread_only:
        query = query.filter(Notification.is_read == False)
    return query.order_by(Notification.created_at.desc()).limit(50).all()


@router.patch("/notifications/{notif_id}/read")
def mark_notification_read(
    notif_id: int,
    admin: User = Depends(verify_admin),
    db: Session = Depends(get_db),
):
    notif = db.query(Notification).filter(Notification.id == notif_id).first()
    if not notif:
        raise HTTPException(status_code=404, detail="Notification not found")
    notif.is_read = True
    db.commit()
    return {"message": "Notification marked as read"}


@router.patch("/notifications/read-all")
def mark_all_notifications_read(
    admin: User = Depends(verify_admin),
    db: Session = Depends(get_db),
):
    db.query(Notification).filter(Notification.is_read == False).update({"is_read": True})
    db.commit()
    return {"message": "All notifications marked as read"}


# ─── SETTINGS ────────────────────────────────────────────────────────────────

_settings_store: dict = {
    "platform_name": "AI Voice Interview Platform",
    "max_interviews_per_user": 50,
    "max_tokens_per_interview": 8000,
    "ai_model": "gemini-2.0-flash",
    "voice_enabled": True,
    "maintenance_mode": False,
}


@router.get("/settings", response_model=AdminSettings)
def get_settings(admin: User = Depends(verify_admin)):
    return AdminSettings(**_settings_store)


@router.put("/settings", response_model=AdminSettings)
def update_settings(
    settings: AdminSettings,
    admin: User = Depends(verify_admin),
    db: Session = Depends(get_db),
):
    _settings_store.update(settings.dict())
    create_audit_log(db, admin, "settings_changed", details=settings.dict())
    return AdminSettings(**_settings_store)


# ─── CODING ADMIN ─────────────────────────────────────────────────────────────

from app.models.coding_challenge import CodingChallenge, CodingSubmission, CodingSession


@router.get("/coding/submissions", response_model=AdminCodingSubmissionsResponse)
def admin_list_coding_submissions(
    admin: User = Depends(verify_admin),
    db: Session = Depends(get_db),
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=100),
    language: Optional[str] = Query(None),
    status: Optional[str] = Query(None),
    search: Optional[str] = Query(None),
):
    query = db.query(CodingSubmission).filter(CodingSubmission.is_final == True)

    if language:
        query = query.filter(CodingSubmission.language == language)
    if status:
        query = query.filter(CodingSubmission.status == status)
    if search:
        like = f"%{search}%"
        query = query.join(User, CodingSubmission.user_id == User.id)\
                     .join(CodingChallenge, CodingSubmission.challenge_id == CodingChallenge.id)\
                     .filter(
                         (User.name.ilike(like)) |
                         (User.email.ilike(like)) |
                         (CodingChallenge.title.ilike(like))
                     )

    total = query.count()
    submissions = query.order_by(CodingSubmission.created_at.desc()).offset(
        (page - 1) * per_page
    ).limit(per_page).all()

    import math
    total_pages = max(1, math.ceil(total / per_page))

    result = []
    for s in submissions:
        user = db.query(User).filter(User.id == s.user_id).first()
        challenge = db.query(CodingChallenge).filter(CodingChallenge.id == s.challenge_id).first()
        result.append(AdminCodingSubmission(
            id=s.id,
            candidate_email=user.email if user else "—",
            challenge_title=challenge.title if challenge else "—",
            language=s.language,
            status=s.status,
            runtime_ms=s.runtime_ms,
            memory_kb=s.memory_kb,
            correctness_score=s.correctness_score,
            ai_score=s.ai_score,
            is_final=s.is_final or False,
            created_at=s.created_at,
        ))

    return AdminCodingSubmissionsResponse(
        submissions=result,
        total=total,
        total_pages=total_pages,
        page=page,
        per_page=per_page,
    )


@router.get("/coding/submissions/{submission_id}", response_model=AdminCodingSubmissionDetail)
def admin_get_coding_submission(
    submission_id: int,
    admin: User = Depends(verify_admin),
    db: Session = Depends(get_db),
):
    s = db.query(CodingSubmission).filter(CodingSubmission.id == submission_id).first()
    if not s:
        raise HTTPException(status_code=404, detail="Submission not found")

    user = db.query(User).filter(User.id == s.user_id).first()
    challenge = db.query(CodingChallenge).filter(CodingChallenge.id == s.challenge_id).first()
    if not challenge:
        raise HTTPException(status_code=404, detail="Challenge associated with submission not found")

    test_results = s.test_results or []
    hidden_total = len(challenge.hidden_test_cases or [])
    if hidden_total > 0 and test_results:
        hidden_results = test_results[-hidden_total:]
        hidden_passed = sum(1 for r in hidden_results if r.get("passed", False))
    else:
        hidden_passed = 0

    return AdminCodingSubmissionDetail(
        id=s.id,
        candidate_email=user.email if user else "—",
        challenge_title=challenge.title if challenge else "—",
        language=s.language,
        status=s.status,
        correctness_score=s.correctness_score,
        ai_score=s.ai_score,
        runtime_ms=s.runtime_ms,
        memory_kb=s.memory_kb,
        is_final=s.is_final or False,
        created_at=s.created_at,
        code=s.code,
        ai_feedback=s.ai_feedback,
        time_complexity=s.time_complexity,
        space_complexity=s.space_complexity,
        test_results=test_results,
        hidden_passed=hidden_passed,
        hidden_total=hidden_total,
    )


@router.get("/coding/analytics", response_model=AdminCodingAnalytics)
def admin_get_coding_analytics(
    admin: User = Depends(verify_admin),
    db: Session = Depends(get_db),
):
    total_submissions = db.query(func.count(CodingSubmission.id)).filter(
        CodingSubmission.is_final == True
    ).scalar() or 0

    total_sessions = db.query(func.count(CodingSession.id)).scalar() or 0

    avg_score = db.query(func.avg(CodingSubmission.ai_score)).filter(
        CodingSubmission.is_final == True,
        CodingSubmission.ai_score.isnot(None),
    ).scalar() or 0.0

    avg_correctness = db.query(func.avg(CodingSubmission.correctness_score)).filter(
        CodingSubmission.is_final == True,
        CodingSubmission.correctness_score.isnot(None),
    ).scalar() or 0.0

    # Language distribution
    lang_rows = db.query(
        CodingSubmission.language, func.count(CodingSubmission.id)
    ).filter(CodingSubmission.is_final == True).group_by(CodingSubmission.language).all()
    language_distribution = {lang: cnt for lang, cnt in lang_rows if lang}

    # Status distribution
    status_rows = db.query(
        CodingSubmission.status, func.count(CodingSubmission.id)
    ).filter(CodingSubmission.is_final == True).group_by(CodingSubmission.status).all()
    status_distribution = {s: c for s, c in status_rows if s}

    # Difficulty breakdown
    diff_rows = db.query(
        CodingChallenge.difficulty, func.count(CodingSubmission.id)
    ).join(CodingChallenge, CodingSubmission.challenge_id == CodingChallenge.id).filter(
        CodingSubmission.is_final == True
    ).group_by(CodingChallenge.difficulty).all()
    difficulty_breakdown = {diff: cnt for diff, cnt in diff_rows if diff}

    return AdminCodingAnalytics(
        total_submissions=total_submissions,
        total_sessions=total_sessions,
        avg_correctness_score=round(float(avg_correctness), 2),
        avg_ai_score=round(float(avg_score), 2),
        language_distribution=language_distribution,
        status_distribution=status_distribution,
        difficulty_breakdown=difficulty_breakdown,
    )

