"""ATS score prediction model — enhanced with NER-derived heuristic."""

import json
import os
from typing import Optional
import joblib
import numpy as np

from app.ml.config import ATS_MODEL_PATH, ATS_KNOWLEDGE_PATH


def _load_ats_knowledge() -> dict:
    try:
        with open(ATS_KNOWLEDGE_PATH, "r") as f:
            return json.load(f)
    except FileNotFoundError:
        return {}


_ATS_KB = None


def _get_ats_kb() -> dict:
    global _ATS_KB
    if _ATS_KB is None:
        _ATS_KB = _load_ats_knowledge()
    return _ATS_KB


class ATSPredictor:
    """Predict ATS score using XGBoost regression model with NER-informed heuristic fallback."""

    _model = None
    _loaded = False
    _model_feature_count = 10  # tracks whether loaded model uses 10 or 16 features

    FEATURE_NAMES_16 = [
        "resume_length", "section_count", "skill_count", "experience_years",
        "project_count", "education_level", "certification_count",
        "keyword_density", "section_completeness", "action_verb_density",
        "has_contact_info", "has_experience_section", "has_education_section",
        "has_skills_section", "designation_count", "company_count",
    ]

    FEATURE_NAMES_10 = FEATURE_NAMES_16[:10]

    @classmethod
    def _load(cls):
        if cls._loaded:
            return
        if os.path.exists(ATS_MODEL_PATH):
            try:
                data = joblib.load(ATS_MODEL_PATH)
                cls._model = data["model"]
                cls._loaded = True
                cls._model_feature_count = data.get("feature_count", 10)
            except Exception as e:
                print(f"[ML] Failed to load ATS model: {e}")

    @classmethod
    def predict(cls, features: dict) -> dict:
        cls._load()
        if cls._model is None:
            return cls._heuristic_predict(features)

        try:
            if cls._model_feature_count >= 16:
                feature_vector = [float(features.get(name, 0)) for name in cls.FEATURE_NAMES_16]
            else:
                feature_vector = [float(features.get(name, 0)) for name in cls.FEATURE_NAMES_10]

            X = np.array([feature_vector])
            score = float(cls._model.predict(X)[0])
            score = max(0, min(100, score))

            confidence = 85.0
            if hasattr(cls._model, "estimators_"):
                preds = np.array([tree.predict(X)[0] for tree in cls._model.estimators_])
                std = float(np.std(preds))
                confidence = max(70, min(98, 95 - std * 2))

            return {
                "ats_score": round(score, 1),
                "confidence": round(confidence, 1),
            }
        except Exception as e:
            print(f"[ML] ATS prediction error: {e}")
            return cls._heuristic_predict(features)

    @staticmethod
    def _heuristic_predict(features: dict) -> dict:
        """NER-informed heuristic ATS scoring.

        Weights derived from analyzing 220 annotated resumes:
        - Skill count is the strongest signal (skills section presence + count)
        - Experience years and education level matter significantly
        - Contact info, section structure, and action verbs add quality signal
        - Keyword density is critical for job-description matching
        """
        kb = _get_ats_kb()
        exp_range = kb.get("experience_range", {})
        avg_exp = exp_range.get("avg", 5)

        score = 30.0  # base

        # ── Skill quality (0-25 pts) ──
        skill_count = features.get("skill_count", 0)
        has_skills_section = features.get("has_skills_section", 0)
        if skill_count >= 8:
            score += 20
        elif skill_count >= 5:
            score += 15
        elif skill_count >= 3:
            score += 10
        elif skill_count >= 1:
            score += 5
        if has_skills_section:
            score += 5

        # ── Experience (0-15 pts) ──
        exp_years = features.get("experience_years", 0)
        has_exp_section = features.get("has_experience_section", 0)
        if exp_years > 0:
            if exp_years >= 3:
                score += 12
            elif exp_years >= 1:
                score += 8
            else:
                score += 4
        if has_exp_section:
            score += 3

        # ── Education (0-10 pts) ──
        edu_level = features.get("education_level", 0)
        has_edu_section = features.get("has_education_section", 0)
        if edu_level >= 4:
            score += 10
        elif edu_level >= 3:
            score += 8
        elif edu_level >= 2:
            score += 5
        elif edu_level >= 1:
            score += 3
        if has_edu_section:
            score += 2

        # ── Structure & completeness (0-12 pts) ──
        section_comp = features.get("section_completeness", 0)
        section_count = features.get("section_count", 0)
        word_count = features.get("resume_length", 0)
        score += section_comp * 8
        if section_count >= 4:
            score += 4
        elif section_count >= 3:
            score += 3
        elif section_count >= 2:
            score += 2
        # Optimal length: 200-1000 words
        if 200 <= word_count <= 1000:
            score += 2
        elif word_count < 100:
            score -= 5

        # ── Contact info (0-5 pts) ──
        has_contact = features.get("has_contact_info", 0)
        score += has_contact * 5

        # ── Designations & companies (0-6 pts) ──
        des_count = features.get("designation_count", 0)
        comp_count = features.get("company_count", 0)
        if des_count >= 2:
            score += 3
        elif des_count >= 1:
            score += 2
        if comp_count >= 2:
            score += 3
        elif comp_count >= 1:
            score += 2

        # ── Action verbs & quality (0-5 pts) ──
        action_density = features.get("action_verb_density", 0)
        if action_density > 0.03:
            score += 5
        elif action_density > 0.015:
            score += 3
        elif action_density > 0.005:
            score += 1

        cert_count = features.get("certification_count", 0)
        if cert_count >= 2:
            score += 3
        elif cert_count >= 1:
            score += 1

        # ── Keyword density (job match) (0-10 pts) ──
        keyword_density = features.get("keyword_density", 0)
        score += keyword_density * 10

        # ── Projects (0-4 pts) ──
        project_count = features.get("project_count", 0)
        if project_count >= 3:
            score += 4
        elif project_count >= 1:
            score += 2

        score = max(15, min(98, score))
        return {
            "ats_score": round(score, 1),
            "confidence": 75.0,
        }
