"""ML API routes — all endpoints under /ml/ prefix."""

import json
import time
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, validator
from sqlalchemy.orm import Session

from app.database import get_db
from app.auth.utils import get_current_user
from app.models.user import User
from app.models.resume import Resume
from app.models.ml_analytics import (
    MLClassification, MLATSPrediction, MLSkillExtraction,
    MLJobRecommendation, MLResumeEmbedding, MLSearchLog,
    MLQualityPrediction, MLAnalysisHistory,
)

router = APIRouter(prefix="/ml", tags=["ML"])


# ── Request / Response Schemas ──

class ResumeIDRequest(BaseModel):
    resume_id: int

class JDTextRequest(BaseModel):
    resume_id: int
    job_description_id: Optional[int] = None

class SkillGapRequest(BaseModel):
    resume_id: int
    job_description_id: int

class RankRequest(BaseModel):
    resume_ids: list[int]
    job_description_id: int

    @validator("resume_ids")
    def validate_resume_ids(cls, v):
        if len(v) > 50:
            raise ValueError("Cannot rank more than 50 resumes at once")
        if len(v) == 0:
            raise ValueError("At least one resume_id is required")
        return v

class SearchRequest(BaseModel):
    query: str
    top_k: Optional[int] = 10

    @validator("query")
    def validate_query(cls, v):
        if len(v) > 10000:
            raise ValueError("Query too long (max 10000 characters)")
        return v

    @validator("top_k")
    def validate_top_k(cls, v):
        if v is not None and (v < 1 or v > 100):
            raise ValueError("top_k must be between 1 and 100")
        return v

class RecommendSkillsRequest(BaseModel):
    resume_id: int
    target_role: Optional[str] = ""

class CareerPathRequest(BaseModel):
    resume_id: int
    current_role: Optional[str] = ""

class FullAnalysisRequest(BaseModel):
    resume_id: int
    job_description_id: Optional[int] = None


# ── Helper ──

def _get_resume_text(resume_id: int, user_id: int, db: Session) -> str:
    resume = db.query(Resume).filter(Resume.id == resume_id, Resume.user_id == user_id).first()
    if not resume:
        raise HTTPException(status_code=404, detail="Resume not found")
    if not resume.extracted_text:
        raise HTTPException(status_code=400, detail="Resume has no extracted text")
    return resume.extracted_text


def _get_jd_text(jd_id: int, user_id: int, db: Session) -> str:
    from app.models.career import JobDescription
    jd = db.query(JobDescription).filter(JobDescription.id == jd_id, JobDescription.user_id == user_id).first()
    if not jd:
        raise HTTPException(status_code=404, detail="Job description not found")
    return jd.raw_text or ""


def _store_history(user_id: int, resume_id: int, analysis_type: str, result: dict, db: Session):
    try:
        record = MLAnalysisHistory(
            user_id=user_id,
            resume_id=resume_id,
            analysis_type=analysis_type,
            result_json=json.dumps(result),
        )
        db.add(record)
        db.commit()
    except Exception:
        db.rollback()


# ── Endpoints ──

@router.post("/classify")
def classify_resume(req: ResumeIDRequest, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    start = time.time()
    resume_text = _get_resume_text(req.resume_id, user.id, db)

    from app.ml.prediction.classifier_service import ClassifierService
    result = ClassifierService.classify(resume_text)
    result["latency_ms"] = round((time.time() - start) * 1000, 1)

    try:
        record = MLClassification(
            user_id=user.id, resume_id=req.resume_id,
            predicted_role=result["predicted_role"], confidence=result["confidence"],
        )
        db.add(record)
        db.commit()
    except Exception:
        db.rollback()

    _store_history(user.id, req.resume_id, "classify", result, db)
    return result


@router.post("/extract-skills")
def extract_skills(req: ResumeIDRequest, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    start = time.time()
    resume_text = _get_resume_text(req.resume_id, user.id, db)

    from app.ml.prediction.skill_service import SkillService
    result = SkillService.extract_skills(resume_text)
    result["latency_ms"] = round((time.time() - start) * 1000, 1)

    try:
        record = MLSkillExtraction(
            user_id=user.id, resume_id=req.resume_id,
            skills_json=json.dumps(result),
        )
        db.add(record)
        db.commit()
    except Exception:
        db.rollback()

    _store_history(user.id, req.resume_id, "extract-skills", result, db)
    return result


@router.post("/predict-ats")
def predict_ats(req: JDTextRequest, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    start = time.time()
    resume_text = _get_resume_text(req.resume_id, user.id, db)
    jd_text = ""
    if req.job_description_id:
        jd_text = _get_jd_text(req.job_description_id, user.id, db)

    from app.ml.prediction.ats_service import ATSService
    result = ATSService.predict_ats(resume_text, jd_text)
    result["latency_ms"] = round((time.time() - start) * 1000, 1)

    try:
        record = MLATSPrediction(
            user_id=user.id, resume_id=req.resume_id,
            ats_score=result["ats_score"], confidence=result["confidence"],
        )
        db.add(record)
        db.commit()
    except Exception:
        db.rollback()

    _store_history(user.id, req.resume_id, "predict-ats", result, db)
    return result


@router.post("/skill-gap")
def skill_gap_analysis(req: SkillGapRequest, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    start = time.time()
    resume_text = _get_resume_text(req.resume_id, user.id, db)
    jd_text = _get_jd_text(req.job_description_id, user.id, db)

    from app.ml.prediction.skill_service import SkillService
    result = SkillService.skill_gap(resume_text, jd_text)
    result["latency_ms"] = round((time.time() - start) * 1000, 1)

    _store_history(user.id, req.resume_id, "skill-gap", result, db)
    return result


@router.post("/recommend-jobs")
def recommend_jobs(req: ResumeIDRequest, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    start = time.time()
    resume_text = _get_resume_text(req.resume_id, user.id, db)

    from app.ml.prediction.recommender_service import RecommenderService
    jobs = RecommenderService.recommend_jobs(resume_text)
    result = {"recommendations": jobs, "latency_ms": round((time.time() - start) * 1000, 1)}

    try:
        record = MLJobRecommendation(
            user_id=user.id, resume_id=req.resume_id,
            recommendations_json=json.dumps(jobs),
        )
        db.add(record)
        db.commit()
    except Exception:
        db.rollback()

    _store_history(user.id, req.resume_id, "recommend-jobs", result, db)
    return result


@router.post("/rank-resumes")
def rank_resumes(req: RankRequest, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    start = time.time()
    jd_text = _get_jd_text(req.job_description_id, user.id, db)
    resume_texts = []
    for rid in req.resume_ids:
        resume = db.query(Resume).filter(Resume.id == rid).first()
        if resume and resume.extracted_text:
            resume_texts.append({
                "resume_id": rid,
                "filename": resume.filename,
                "resume_text": resume.extracted_text,
            })

    from app.ml.prediction.recommender_service import RecommenderService
    rankings = RecommenderService.rank_resumes(resume_texts, jd_text)
    result = {"rankings": rankings, "latency_ms": round((time.time() - start) * 1000, 1)}
    return result


@router.post("/search")
def semantic_search(req: SearchRequest, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    start = time.time()

    from app.ml.prediction.search_service import SearchService
    results = SearchService.search(req.query, top_k=req.top_k)
    result = {"results": results, "latency_ms": round((time.time() - start) * 1000, 1)}

    try:
        record = MLSearchLog(
            user_id=user.id, query_text=req.query,
            results_json=json.dumps(results),
        )
        db.add(record)
        db.commit()
    except Exception:
        db.rollback()

    return result


@router.post("/career-path")
def career_path(req: CareerPathRequest, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    start = time.time()
    resume_text = _get_resume_text(req.resume_id, user.id, db)

    from app.ml.prediction.recommender_service import RecommenderService
    result = RecommenderService.career_path(resume_text, req.current_role or "")
    result["latency_ms"] = round((time.time() - start) * 1000, 1)

    _store_history(user.id, req.resume_id, "career-path", result, db)
    return result


@router.post("/quality")
def predict_quality(req: ResumeIDRequest, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    start = time.time()
    resume_text = _get_resume_text(req.resume_id, user.id, db)

    from app.ml.prediction.recommender_service import RecommenderService
    result = RecommenderService.predict_quality(resume_text)
    result["latency_ms"] = round((time.time() - start) * 1000, 1)

    try:
        record = MLQualityPrediction(
            user_id=user.id, resume_id=req.resume_id,
            quality=result["quality"], confidence=result["confidence"],
        )
        db.add(record)
        db.commit()
    except Exception:
        db.rollback()

    _store_history(user.id, req.resume_id, "quality", result, db)
    return result


@router.post("/recommend-skills")
def recommend_skills(req: RecommendSkillsRequest, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    start = time.time()
    resume_text = _get_resume_text(req.resume_id, user.id, db)

    from app.ml.prediction.skill_service import SkillService
    result = SkillService.recommend_skills(resume_text, req.target_role or "")
    result["latency_ms"] = round((time.time() - start) * 1000, 1)

    _store_history(user.id, req.resume_id, "recommend-skills", result, db)
    return result


@router.post("/analyze-full")
def full_analysis(req: FullAnalysisRequest, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    start = time.time()
    resume_text = _get_resume_text(req.resume_id, user.id, db)
    jd_text = ""
    if req.job_description_id:
        jd_text = _get_jd_text(req.job_description_id, user.id, db)

    from app.ml.prediction.classifier_service import ClassifierService
    from app.ml.prediction.skill_service import SkillService
    from app.ml.prediction.ats_service import ATSService
    from app.ml.prediction.recommender_service import RecommenderService

    classification = ClassifierService.classify(resume_text)
    skills = SkillService.extract_skills(resume_text)
    ats = ATSService.predict_ats(resume_text, jd_text)
    jobs = RecommenderService.recommend_jobs(resume_text)
    quality = RecommenderService.predict_quality(resume_text)
    career = RecommenderService.career_path(resume_text, classification.get("predicted_role", ""))
    recommend_skills = SkillService.recommend_skills(resume_text, classification.get("predicted_role", ""))

    skill_gap = None
    if jd_text:
        skill_gap = SkillService.skill_gap(resume_text, jd_text)

    total_latency = round((time.time() - start) * 1000, 1)

    result = {
        "classification": classification,
        "skills": skills,
        "ats_prediction": ats,
        "job_recommendations": jobs,
        "quality": quality,
        "career_path": career,
        "recommended_skills": recommend_skills,
        "skill_gap": skill_gap,
        "total_latency_ms": total_latency,
    }

    _store_history(user.id, req.resume_id, "analyze-full", result, db)
    return result


@router.get("/history")
def get_history(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    records = (
        db.query(MLAnalysisHistory)
        .filter(MLAnalysisHistory.user_id == user.id)
        .order_by(MLAnalysisHistory.created_at.desc())
        .limit(50)
        .all()
    )
    return [
        {
            "id": r.id,
            "resume_id": r.resume_id,
            "analysis_type": r.analysis_type,
            "result": json.loads(r.result_json) if r.result_json else {},
            "created_at": r.created_at.isoformat() if r.created_at else None,
        }
        for r in records
    ]


@router.get("/analytics")
def get_analytics(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    classifications = (
        db.query(MLClassification)
        .filter(MLClassification.user_id == user.id)
        .all()
    )
    ats_predictions = (
        db.query(MLATSPrediction)
        .filter(MLATSPrediction.user_id == user.id)
        .all()
    )
    quality_predictions = (
        db.query(MLQualityPrediction)
        .filter(MLQualityPrediction.user_id == user.id)
        .all()
    )

    role_dist = {}
    for c in classifications:
        role_dist[c.predicted_role] = role_dist.get(c.predicted_role, 0) + 1

    avg_ats = sum(a.ats_score for a in ats_predictions) / len(ats_predictions) if ats_predictions else 0
    avg_quality_conf = sum(q.confidence for q in quality_predictions) / len(quality_predictions) if quality_predictions else 0

    quality_dist = {}
    for q in quality_predictions:
        quality_dist[q.quality] = quality_dist.get(q.quality, 0) + 1

    return {
        "total_classifications": len(classifications),
        "total_ats_predictions": len(ats_predictions),
        "total_quality_predictions": len(quality_predictions),
        "role_distribution": role_dist,
        "quality_distribution": quality_dist,
        "average_ats_score": round(avg_ats, 1),
        "average_quality_confidence": round(avg_quality_conf, 1),
    }
