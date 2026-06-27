"""ML-trained job recommendation model using XGBoost + TF-IDF."""

import os
import re
import joblib
import numpy as np
from app.ml.config import RECOMMENDER_MODEL_PATH, JOB_ROLES_PATH
import json


class JobRecommenderModel:
    """XGBoost-based job role classifier trained on 2,483 real resumes.

    Uses TF-IDF features (3000-dim) from resume text to predict
    one of 23 job categories. Falls back to None if model unavailable.
    """

    _data = None

    @classmethod
    def _load(cls):
        if cls._data is not None:
            return True
        if not os.path.exists(RECOMMENDER_MODEL_PATH):
            return False
        try:
            cls._data = joblib.load(RECOMMENDER_MODEL_PATH)
            return True
        except Exception:
            return False

    @classmethod
    def predict(cls, resume_text: str, top_k: int = 5) -> list[dict] | None:
        """Predict job role recommendations from resume text.

        Returns list of {role, score, confidence} dicts, or None if model unavailable.
        """
        if not cls._load():
            return None

        try:
            cleaned = re.sub(r"\s+", " ", resume_text.lower()).strip()
            if len(cleaned) < 20:
                return None

            tfidf = cls._data["tfidf"]
            model = cls._data["model"]
            le = cls._data["label_encoder"]

            X = tfidf.transform([cleaned]).toarray().astype(np.float32)
            proba = model.predict_proba(X)[0]

            top_indices = np.argsort(proba)[::-1][:top_k]

            results = []
            for idx in top_indices:
                role_name = le.inverse_transform([idx])[0]
                confidence = float(proba[idx])

                if confidence < 0.05:
                    continue

                score = round(confidence * 100, 1)

                role_data = cls._get_role_metadata(role_name)
                results.append({
                    "role": role_name,
                    "score": score,
                    "confidence": round(confidence * 100, 1),
                    "description": role_data.get("description", ""),
                    "core_skills": role_data.get("core_skills", []),
                    "secondary_skills": role_data.get("secondary_skills", []),
                    "source": "ml_model",
                })

            return results

        except Exception:
            return None

    @classmethod
    def _get_role_metadata(cls, role_name: str) -> dict:
        """Get role metadata from job_roles.json if available."""
        try:
            with open(JOB_ROLES_PATH, "r") as f:
                data = json.load(f)
            roles = data.get("roles", {})
            if role_name in roles:
                return roles[role_name]
            for key, val in roles.items():
                if key.lower() == role_name.lower():
                    return val
        except Exception:
            pass
        return {}

    @classmethod
    def get_info(cls) -> dict:
        """Return model metadata."""
        if not cls._load():
            return {"loaded": False}
        return {
            "loaded": True,
            "metrics": cls._data.get("metrics", {}),
            "n_classes": len(cls._data.get("class_names", [])),
            "n_features": cls._data.get("metrics", {}).get("n_features", 0),
        }
