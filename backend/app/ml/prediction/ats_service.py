"""ML-based ATS prediction service."""

from app.ml.models.ats_predictor import ATSPredictor
from app.ml.utils.feature_engineer import FeatureEngineer


class ATSService:
    """High-level service for ML-based ATS score prediction."""

    @staticmethod
    def predict_ats(resume_text: str, jd_text: str = "") -> dict:
        features = FeatureEngineer.extract_all_features(resume_text, jd_text)
        return ATSPredictor.predict(features)

    @staticmethod
    def predict_ats_with_features(features: dict) -> dict:
        return ATSPredictor.predict(features)
