"""Career path recommendation engine."""

import json
import os
import numpy as np
from typing import Optional

from app.ml.config import CAREER_PATHS_PATH
from app.ml.embeddings.embedder import Embedder
from app.ml.models.skill_extractor import SkillExtractor


class CareerPathEngine:
    """Recommend career progression paths based on current role and skills."""

    _paths = None

    @classmethod
    def _load_paths(cls):
        if cls._paths is None:
            try:
                with open(CAREER_PATHS_PATH, "r") as f:
                    data = json.load(f)
                cls._paths = data.get("career_paths", {})
            except FileNotFoundError:
                cls._paths = {}

    @classmethod
    def recommend(cls, resume_text: str, current_role: str = "") -> dict:
        cls._load_paths()
        if not cls._paths:
            return {"current_role": current_role or "Unknown", "recommended_paths": []}

        if not current_role:
            from app.ml.models.resume_classifier import ResumeClassifier
            result = ResumeClassifier.predict(resume_text)
            current_role = result.get("predicted_role", "Backend Developer")

        role_data = cls._paths.get(current_role)
        if not role_data:
            closest = cls._find_closest_role(current_role)
            role_data = cls._paths.get(closest, {})

        current_skills = SkillExtractor.extract(resume_text)
        current_skill_set = set(current_skills.get("all_skills", []))

        recommendations = []
        for path_type in ["senior", "lateral", "advanced"]:
            targets = role_data.get(path_type, [])
            for target_role in targets:
                gap_skills = role_data.get("skill_progression", {}).get(target_role, [])
                matching = [s for s in gap_skills if s in current_skill_set]
                missing = [s for s in gap_skills if s not in current_skill_set]

                match_pct = (len(matching) / len(gap_skills) * 100) if gap_skills else 50

                if path_type == "senior":
                    level_boost = 20
                elif path_type == "lateral":
                    level_boost = 10
                else:
                    level_boost = 0

                match_score = min(98, match_pct + level_boost)

                recommendations.append({
                    "role": target_role,
                    "path_type": path_type,
                    "match_score": round(match_score, 1),
                    "gap_skills": missing,
                    "matching_skills": matching,
                })

        recommendations.sort(key=lambda x: x["match_score"], reverse=True)
        return {
            "current_role": current_role,
            "recommended_paths": recommendations[:6],
        }

    @classmethod
    def _find_closest_role(cls, role: str) -> str:
        role_lower = role.lower()
        best_match = ""
        try:
            all_roles = [role_lower] + [r.lower() for r in cls._paths]
            all_embeddings = Embedder.encode_batch(all_roles)
            role_embedding = all_embeddings[0:1]
            path_embeddings = all_embeddings[1:]
            scores = Embedder.cosine_similarities(role_embedding, path_embeddings)
            best_idx = int(np.argmax(scores))
            best_score = float(scores[best_idx])
            if best_score > 0:
                best_match = list(cls._paths.keys())[best_idx]
        except (RuntimeError, ValueError, IndexError):
            for path_role in cls._paths:
                if role_lower in path_role.lower() or path_role.lower() in role_lower:
                    best_match = path_role
                    break
        return best_match
