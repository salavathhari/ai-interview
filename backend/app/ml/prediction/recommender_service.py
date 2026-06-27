"""Job recommendation, career path, quality prediction, and ranking services."""

from app.ml.models.job_recommender import JobRecommender
from app.ml.models.career_path import CareerPathEngine
from app.ml.models.quality_predictor import QualityPredictor
from app.ml.utils.feature_engineer import FeatureEngineer


class RecommenderService:
    """High-level service for recommendations and ranking."""

    @staticmethod
    def recommend_jobs(resume_text: str, top_k: int = 5) -> list[dict]:
        return JobRecommender.recommend(resume_text, top_k=top_k)

    @staticmethod
    def career_path(resume_text: str, current_role: str = "") -> dict:
        return CareerPathEngine.recommend(resume_text, current_role)

    @staticmethod
    def predict_quality(resume_text: str) -> dict:
        features = FeatureEngineer.extract_all_features(resume_text)
        return QualityPredictor.predict(features)

    @staticmethod
    def rank_resumes(resume_texts: list[dict], jd_text: str) -> list[dict]:
        ranked = []
        for item in resume_texts:
            resume_text = item.get("resume_text", "")
            resume_id = item.get("resume_id")
            filename = item.get("filename", "")

            features = FeatureEngineer.extract_all_features(resume_text, jd_text)
            from app.ml.models.ats_predictor import ATSPredictor
            ats_result = ATSPredictor.predict(features)
            ats_score = ats_result.get("ats_score", 50)

            from app.ml.models.skill_extractor import SkillExtractor
            resume_skills = set(SkillExtractor.extract(resume_text).get("all_skills", []))
            jd_skills = set(SkillExtractor.extract(jd_text).get("all_skills", []))
            skill_match = (len(resume_skills & jd_skills) / max(len(jd_skills), 1) * 100) if jd_skills else 50

            exp_score = min(features.get("experience_years", 0) * 10, 100)
            edu_score = features.get("education_level", 0) * 20
            project_score = min(features.get("project_count", 0) * 15, 100)

            composite = (
                ats_score * 0.30 +
                skill_match * 0.30 +
                exp_score * 0.20 +
                edu_score * 0.10 +
                project_score * 0.10
            )

            ranked.append({
                "resume_id": resume_id,
                "filename": filename,
                "score": round(composite, 1),
                "ats_score": round(ats_score, 1),
                "skill_match": round(skill_match, 1),
            })

        ranked.sort(key=lambda x: x["score"], reverse=True)
        for i, item in enumerate(ranked):
            item["rank"] = i + 1

        return ranked
