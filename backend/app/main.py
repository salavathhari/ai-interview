from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from app.core.middleware import monitoring_middleware
from app.database import engine, Base, init_models
from app.models.user import User
from app.models.interview_session import InterviewSession
from app.models.resume import Resume
from app.models.question import Question
from app.models.interview_question_metric import InterviewQuestionMetric
from app.models.coding_challenge import CodingChallenge, CodingSubmission, CodingSession
from app.models.cheating_log import CheatingLog
from app.models.job_role import JobRole
from app.models.api_usage import ApiUsage
from app.models.admin_log import AdminLog
from app.models.system_health_log import SystemHealthLog
from app.models.notification import Notification
from app.models.message import Message
from app.models.ats_report import ATSReport
from app.models.ml_analytics import (
    MLClassification, MLATSPrediction, MLSkillExtraction,
    MLJobRecommendation, MLResumeEmbedding, MLSearchLog,
    MLQualityPrediction, MLAnalysisHistory,
)
from app.routes.auth import router as auth_router
from app.routes.users import router as users_router
from app.routes.resumes import router as resumes_router
from app.routes.interviews import router as interviews_router
from app.routes.websocket import router as ws_router
from app.routes.analytics import router as analytics_router
from app.routes.coding import router as coding_router
from app.routes.admin import router as admin_router
from app.routes.recruiter import router as recruiter_router
from app.routes.recruiter_v2 import router as recruiter_v2_router
from app.routes.career import router as career_router
from app.routes.ats import router as ats_router
from app.routes.ml import router as ml_router
from app.routes.reports import router as reports_router
from app.routes.candidate_jobs import router as candidate_jobs_router
from app.routes.chat import router as chat_router
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.gzip import GZipMiddleware
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from app.core.rate_limit import limiter
from app.auth.utils import CSRF_COOKIE_NAME

import traceback


def _is_production() -> bool:
    import os
    return os.getenv("ENVIRONMENT", "development").lower() == "production"

Base.metadata.create_all(bind=engine)
init_models()

app = FastAPI()
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# Add GZIP compression for responses > 500 bytes
app.add_middleware(GZipMiddleware, minimum_size=500)

# Explicit CORS origins to avoid browser CORS failures during local dev
allowed_origins = [
    "http://localhost:3000",
    "http://localhost:5173",
    "http://localhost:5174",
    "http://127.0.0.1:3000",
    "http://127.0.0.1:5173",
    "http://127.0.0.1:5174",
    "https://ai-interview-frontend.up.railway.app",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_origin_regex=r"https://(ai-interview-frontend\.up\.railway\.app|.*\.vercel\.app|.*\.web\.app|.*\.firebaseapp\.com)$",
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
    allow_headers=["*"],
    max_age=3600,
)


@app.middleware("http")
async def add_security_headers(request: Request, call_next):
    response = await call_next(request)
    if request.url.path.startswith("/ws/"):
        return response
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
    response.headers["Permissions-Policy"] = "camera=(), microphone=(), geolocation=()"
    if _is_production():
        response.headers["Strict-Transport-Security"] = "max-age=63072000; includeSubDomains"
        response.headers["Content-Security-Policy"] = "default-src 'self'; script-src 'self' 'unsafe-inline'; style-src 'self' 'unsafe-inline'; img-src 'self' data: blob:; connect-src 'self' wss:"
    return response


@app.middleware("http")
async def add_monitoring(request: Request, call_next):
    # Skip monitoring for CORS preflight requests to avoid interference
    if request.method == "OPTIONS":
        return await call_next(request)
    return await monitoring_middleware(request, call_next)

# #9: CSRF validation middleware — double-submit cookie pattern
# Validates X-CSRF-Token header matches the csrf_token cookie on state-changing requests.
@app.middleware("http")
async def csrf_protect(request: Request, call_next):
    # Skip CSRF for safe methods, auth endpoints (login/signup set the cookie),
    # and WebSocket connections
    if request.method in ("GET", "HEAD", "OPTIONS"):
        return await call_next(request)
    if request.url.path.startswith("/ws/"):
        return await call_next(request)
    if request.url.path.startswith("/auth/"):
        return await call_next(request)

    # Read CSRF token from cookie
    cookie_csrf = request.cookies.get(CSRF_COOKIE_NAME)
    # Read CSRF token from header
    header_csrf = request.headers.get("X-CSRF-Token")

    # If a CSRF cookie exists, the header must match (double-submit pattern)
    if cookie_csrf:
        if not header_csrf or cookie_csrf != header_csrf:
            return JSONResponse(
                status_code=403,
                content={"detail": "CSRF token mismatch"},
            )

    return await call_next(request)

@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    # #8: Log the full error server-side only — never expose to clients
    print(f"GLOBAL ERROR: {exc}")
    traceback.print_exc()
    # Return a generic error message without leaking internals
    # Include CORS headers directly since middleware may not wrap exception responses
    origin = request.headers.get("origin", "")
    allowed = origin in allowed_origins or any(
        origin.endswith(suffix) for suffix in [".vercel.app", ".web.app", ".firebaseapp.com"]
    ) if origin else False
    headers = {}
    if allowed:
        headers["Access-Control-Allow-Origin"] = origin
        headers["Access-Control-Allow-Credentials"] = "true"
    return JSONResponse(
        status_code=500,
        content={"detail": "An internal error occurred. Please try again later."},
        headers=headers,
    )

app.include_router(auth_router)
app.include_router(users_router)
app.include_router(resumes_router)
app.include_router(interviews_router)
app.include_router(ws_router)
app.include_router(analytics_router)
app.include_router(coding_router)
app.include_router(admin_router)
app.include_router(recruiter_router)
app.include_router(recruiter_v2_router)
app.include_router(candidate_jobs_router)
app.include_router(chat_router)
app.include_router(career_router)
app.include_router(ats_router)
app.include_router(ml_router)
app.include_router(reports_router)

@app.get("/")

def home():
    return {"message": "AI Interview Platform Backend Running"}
