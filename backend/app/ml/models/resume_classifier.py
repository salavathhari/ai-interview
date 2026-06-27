"""TF-IDF + LinearSVC resume classifier."""

import os
import re
from typing import Optional
import joblib
import numpy as np

from app.ml.config import CLASSIFICATION_MODEL_PATH
from app.ml.cache import ml_cache


class ResumeClassifier:
    """Classify resumes into job categories using TF-IDF + LinearSVC."""

    CATEGORIES = [
        "Frontend Developer", "Backend Developer", "Full Stack Developer",
        "Cloud Native Engineer", "DevOps Engineer", "AI Engineer",
        "Data Scientist", "Mobile Developer", "UI/UX Designer", "Cybersecurity Engineer",
    ]

    _model = None
    _vectorizer = None
    _loaded = False

    @classmethod
    def _load(cls):
        if cls._loaded:
            return
        if os.path.exists(CLASSIFICATION_MODEL_PATH):
            try:
                data = joblib.load(CLASSIFICATION_MODEL_PATH)
                cls._model = data["model"]
                cls._vectorizer = data["vectorizer"]
                cls._loaded = True
            except Exception as e:
                print(f"[ML] Failed to load classifier: {e}")
                cls._loaded = False
        else:
            print(f"[ML] Classifier model not found at {CLASSIFICATION_MODEL_PATH}")

    @classmethod
    def predict(cls, resume_text: str) -> dict:
        result, cached = ml_cache.cached("classify", resume_text, cls._predict_uncached)
        return result

    @classmethod
    def _predict_uncached(cls, resume_text: str) -> dict:
        cls._load()
        if cls._model is None or cls._vectorizer is None:
            return cls._heuristic_predict(resume_text)

        cleaned = cls._clean_text(resume_text)
        try:
            features = cls._vectorizer.transform([cleaned])
            prediction = cls._model.predict(features)[0]
            probabilities = None
            if hasattr(cls._model, "predict_proba"):
                probabilities = cls._model.predict_proba(features)[0]
            elif hasattr(cls._model, "decision_function"):
                scores = cls._model.decision_function(features)[0]
                exp_scores = np.exp(scores - np.max(scores))
                probabilities = exp_scores / exp_scores.sum()

            confidence = 0.0
            if probabilities is not None:
                confidence = float(np.max(probabilities)) * 100
            else:
                confidence = 85.0

            return {
                "predicted_role": str(prediction),
                "confidence": round(confidence, 1),
            }
        except Exception as e:
            print(f"[ML] Classification error: {e}")
            return cls._heuristic_predict(resume_text)

    @classmethod
    def _heuristic_predict(cls, resume_text: str) -> dict:
        text_lower = resume_text.lower()
        scores = {}
        role_keywords = {
            "Frontend Developer": ["react", "angular", "vue", "javascript", "typescript", "html", "css", "frontend", "ui", "jsx", "tailwind"],
            "Backend Developer": ["python", "java", "node", "fastapi", "django", "flask", "spring", "api", "backend", "server", "database"],
            "Full Stack Developer": ["full stack", "fullstack", "react", "node", "express", "mongodb", "postgresql", "javascript", "end-to-end"],
            "Cloud Native Engineer": ["aws", "azure", "gcp", "docker", "kubernetes", "terraform", "cloud", "serverless", "microservices"],
            "DevOps Engineer": ["devops", "ci/cd", "jenkins", "github actions", "docker", "kubernetes", "terraform", "ansible", "monitoring"],
            "AI Engineer": ["machine learning", "deep learning", "tensorflow", "pytorch", "nlp", "neural", "ai", "model", "training"],
            "Data Scientist": ["data science", "pandas", "numpy", "statistics", "analysis", "visualization", "sql", "machine learning", "jupyter"],
            "Mobile Developer": ["react native", "flutter", "swift", "kotlin", "android", "ios", "mobile", "app store"],
            "UI/UX Designer": ["figma", "sketch", "adobe xd", "prototyping", "wireframing", "user research", "design", "ux", "ui design"],
            "Cybersecurity Engineer": ["security", "penetration", "vulnerability", "firewall", "siem", "owasp", "cryptography", "incident"],
        }
        for role, keywords in role_keywords.items():
            score = sum(1 for kw in keywords if kw in text_lower)
            scores[role] = score

        best_role = max(scores, key=scores.get)
        best_score = scores[best_role]
        total = sum(scores.values()) or 1
        confidence = (best_score / total * 100) if total > 0 else 50

        return {
            "predicted_role": best_role,
            "confidence": round(min(confidence, 99.0), 1),
        }

    @staticmethod
    def _clean_text(text: str) -> str:
        text = re.sub(r"<[^>]+>", " ", text)
        text = re.sub(r"[^\x00-\x7F]+", " ", text)
        text = re.sub(r"\s+", " ", text)
        return text.strip().lower()
