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
from app.routes.career import router as career_router
from app.routes.ats import router as ats_router
from app.routes.ml import router as ml_router
from app.routes.reports import router as reports_router
from fastapi.middleware.cors import CORSMiddleware
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from app.core.rate_limit import limiter

import traceback

Base.metadata.create_all(bind=engine)
init_models()

app = FastAPI()
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# Explicit CORS origins to avoid browser CORS failures during local dev
allowed_origins = [
    "http://localhost:3000",
    "http://localhost:5173",
    "http://localhost:5174",
    "http://127.0.0.1:3000",
    "http://127.0.0.1:5173",
    "http://127.0.0.1:5174",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
    allow_headers=["*"],
    max_age=3600,
)


@app.middleware("http")
async def add_monitoring(request: Request, call_next):
    # Skip monitoring for CORS preflight requests to avoid interference
    if request.method == "OPTIONS":
        return await call_next(request)
    return await monitoring_middleware(request, call_next)

# Explicit OPTIONS handler — guarantees all preflight requests return 200
@app.options("/{full_path:path}")
async def options_handler(full_path: str):
    return JSONResponse(content={}, status_code=200)

@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    print(f"GLOBAL ERROR: {exc}")
    traceback.print_exc()
    # Include Access-Control-Allow-Origin so browser can surface the error to the client
    origin = request.headers.get("origin") or "*"
    return JSONResponse(
        status_code=500,
        content={"message": "Internal Server Error", "detail": str(exc)},
        headers={"Access-Control-Allow-Origin": origin},
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
app.include_router(career_router)
app.include_router(ats_router)
app.include_router(ml_router)
app.include_router(reports_router)

@app.get("/")

def home():
    return {"message": "AI Interview Platform Backend Running"}
