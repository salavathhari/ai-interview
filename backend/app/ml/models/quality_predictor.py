"""Random Forest resume quality predictor."""

import os
from typing import Optional
import joblib
import numpy as np

from app.ml.config import QUALITY_MODEL_PATH


class QualityPredictor:
    """Predict resume quality as Poor/Average/Good/Excellent."""

    LABELS = ["Poor", "Average", "Good", "Excellent"]
    _model = None
    _loaded = False

    @classmethod
    def _load(cls):
        if cls._loaded:
            return
        if os.path.exists(QUALITY_MODEL_PATH):
            try:
                data = joblib.load(QUALITY_MODEL_PATH)
                cls._model = data["model"]
                cls._loaded = True
            except Exception as e:
                print(f"[ML] Failed to load quality model: {e}")

    @classmethod
    def predict(cls, features: dict) -> dict:
        cls._load()
        if cls._model is None:
            return cls._heuristic_predict(features)

        try:
            feature_vector = [
                float(features.get("resume_length", 0)),
                float(features.get("section_count", 0)),
                float(features.get("skill_count", 0)),
                float(features.get("experience_years", 0)),
                float(features.get("project_count", 0)),
                float(features.get("education_level", 0)),
                float(features.get("certification_count", 0)),
                float(features.get("keyword_density", 0)),
                float(features.get("section_completeness", 0)),
                float(features.get("action_verb_density", 0)),
            ]
            X = np.array([feature_vector])
            prediction = cls._model.predict(X)[0]
            confidence = 80.0
            if hasattr(cls._model, "predict_proba"):
                probs = cls._model.predict_proba(X)[0]
                confidence = float(np.max(probs)) * 100

            return {
                "quality": str(prediction),
                "confidence": round(confidence, 1),
            }
        except Exception as e:
            print(f"[ML] Quality prediction error: {e}")
            return cls._heuristic_predict(features)

    @staticmethod
    def _heuristic_predict(features: dict) -> dict:
        score = 50
        word_count = features.get("resume_length", 0)
        if 300 <= word_count <= 800:
            score += 10
        elif word_count < 150:
            score -= 10

        section_comp = features.get("section_completeness", 0)
        score += int(section_comp * 20)

        skill_count = features.get("skill_count", 0)
        score += min(skill_count, 10)

        exp_years = features.get("experience_years", 0)
        score += min(exp_years * 2, 10)

        edu = features.get("education_level", 0)
        score += edu * 2

        certs = features.get("certification_count", 0)
        score += min(certs * 2, 6)

        keyword_density = features.get("keyword_density", 0)
        score += int(keyword_density * 10)

        action_density = features.get("action_verb_density", 0)
        if action_density > 0.02:
            score += 5

        score = max(0, min(100, score))

        if score < 35:
            quality = "Poor"
        elif score < 55:
            quality = "Average"
        elif score < 75:
            quality = "Good"
        else:
            quality = "Excellent"

        return {
            "quality": quality,
            "confidence": 70.0,
        }
