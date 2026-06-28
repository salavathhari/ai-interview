"""Job role recommendation using ML model + heuristic fallback."""

import json
import re
import os
import numpy as np
from typing import Optional

from app.ml.config import JOB_ROLES_PATH
from app.ml.embeddings.embedder import Embedder


class JobRecommender:
    """Recommend job roles based on resume content.

    Uses a trained XGBoost model (TF-IDF features) as the primary predictor.
    Falls back to semantic similarity + keyword matching if the ML model
    is unavailable or produces low-confidence results.
    """

    _roles = None
    _role_embeddings = None
    _role_skill_sets = None

    @classmethod
    def _load_roles(cls):
        if cls._roles is None:
            try:
                with open(JOB_ROLES_PATH, "r") as f:
                    data = json.load(f)
                cls._roles = data.get("roles", {})
            except FileNotFoundError:
                cls._roles = {}

    @classmethod
    def _build_role_embeddings(cls):
        if cls._role_embeddings is not None:
            return
        cls._load_roles()
        if not cls._roles:
            cls._role_embeddings = {"names": [], "embeddings": []}
            return

        descriptions = []
        names = []
        for role_name, role_data in cls._roles.items():
            desc_parts = [
                role_data.get("description", ""),
                " ".join(role_data.get("core_skills", [])),
                " ".join(role_data.get("secondary_skills", [])),
                " ".join(role_data.get("keywords", [])),
            ]
            descriptions.append(" ".join(desc_parts))
            names.append(role_name)

        try:
            embeddings = Embedder.encode_batch(descriptions)
        except RuntimeError:
            # Embedding model unavailable — use empty embeddings, will fall back to heuristic
            cls._role_embeddings = {"names": names, "embeddings": np.array([])}
            return
        cls._role_embeddings = {
            "names": names,
            "embeddings": embeddings,
        }

    @classmethod
    def _build_role_skill_sets(cls):
        if cls._role_skill_sets is not None:
            return
        cls._load_roles()
        cls._role_skill_sets = {}
        for role_name, role_data in cls._roles.items():
            core = set(s.lower() for s in role_data.get("core_skills", []))
            secondary = set(s.lower() for s in role_data.get("secondary_skills", []))
            keywords = set(s.lower() for s in role_data.get("keywords", []))
            cls._role_skill_sets[role_name] = {
                "core": core,
                "secondary": secondary,
                "keywords": keywords,
                "all": core | secondary | keywords,
            }

    @classmethod
    def _extract_skills_from_text(cls, text: str) -> set:
        text_lower = text.lower()
        SKILL_ALIASES = {
            "python": ["python"], "java": ["java"],
            "javascript": ["javascript", "js"], "typescript": ["typescript", "ts"],
            "c++": ["c++", "cpp"], "c#": ["c#", "csharp"],
            "sql": ["sql"], "html": ["html"], "css": ["css"],
            "react": ["react", "reactjs", "react.js"],
            "node.js": ["node.js", "nodejs", "node"],
            "django": ["django"], "flask": ["flask"], "fastapi": ["fastapi"],
            "aws": ["aws", "amazon web services"],
            "docker": ["docker"], "kubernetes": ["kubernetes", "k8s"],
            "machine learning": ["machine learning", "ml"],
            "deep learning": ["deep learning", "dl"],
            "ai": [" ai ", "ai,", "ai.", "artificial intelligence"],
            "data science": ["data science", "datascience"],
            "nlp": ["nlp", "natural language processing"],
            "tensorflow": ["tensorflow"], "pytorch": ["pytorch"],
            "scikit-learn": ["scikit-learn", "sklearn"],
            "pandas": ["pandas"], "numpy": ["numpy"],
            "git": ["git", "github", "gitlab"], "linux": ["linux"],
            "mongodb": ["mongodb", "mongo"], "postgresql": ["postgresql", "postgres"],
            "mysql": ["mysql"], "redis": ["redis"], "graphql": ["graphql"],
            "rest api": ["rest api", "restful"],
            "spring boot": ["spring boot", "spring"],
            "microservices": ["microservices"],
            "ci/cd": ["ci/cd", "cicd", "continuous integration", "continuous deployment"],
            "terraform": ["terraform"], "ansible": ["ansible"], "jenkins": ["jenkins"],
            "figma": ["figma"], "vue.js": ["vue.js", "vuejs", "vue"],
            "angular": ["angular"], "next.js": ["next.js", "nextjs"],
        }
        found = set()
        for canonical, aliases in SKILL_ALIASES.items():
            for alias in aliases:
                if alias in text_lower:
                    found.add(canonical)
                    break
        return found

    @classmethod
    def _compute_skill_match_score(cls, resume_skills: set, role_name: str) -> dict:
        skill_sets = cls._role_skill_sets.get(role_name, {})
        core_skills = skill_sets.get("core", set())
        secondary_skills = skill_sets.get("secondary", set())
        all_role_skills = skill_sets.get("all", set())

        core_match = resume_skills & core_skills
        secondary_match = resume_skills & secondary_skills
        total_match = resume_skills & all_role_skills

        core_count = len(core_match)
        secondary_count = len(secondary_match)

        max_possible = len(core_skills) * 2 + len(secondary_skills)
        if max_possible > 0:
            score = (core_count * 2 + secondary_count) / max_possible
        else:
            score = 0.0

        return {
            "score": round(score, 3),
            "core_matched": sorted(core_match),
            "secondary_matched": sorted(secondary_match),
            "total_matched": sorted(total_match),
            "core_count": core_count,
            "secondary_count": secondary_count,
        }

    @classmethod
    def recommend(cls, resume_text: str, top_k: int = 5) -> list[dict]:
        """Recommend job roles using ML model with heuristic fallback."""
        from app.ml.models.job_recommender_model import JobRecommenderModel

        ml_results = JobRecommenderModel.predict(resume_text, top_k=top_k)
        if ml_results and ml_results[0]["score"] > 30:
            for r in ml_results:
                r["matched_core_skills"] = []
                r["matched_secondary_skills"] = []
                r["semantic_similarity"] = 0.0
                r["skill_match"] = 0.0
                r["recommendation_rate"] = 0.0
                r["job_variants"] = 0
            return ml_results[:top_k]

        return cls._heuristic_recommend(resume_text, top_k)

    @classmethod
    def _heuristic_recommend(cls, resume_text: str, top_k: int = 5) -> list[dict]:
        """Fallback: semantic similarity + keyword matching."""
        cls._build_role_embeddings()
        cls._build_role_skill_sets()

        if not cls._role_embeddings["names"]:
            return []

        resume_skills = cls._extract_skills_from_text(resume_text)

        try:
            resume_embedding = Embedder.encode(resume_text)
        except RuntimeError:
            # Embedding model unavailable — fall back to pure skill matching
            return cls._skill_only_recommend(resume_skills, top_k)
        role_embeddings = np.array(cls._role_embeddings["embeddings"])
        if role_embeddings.size == 0:
            return cls._skill_only_recommend(resume_skills, top_k)
        query = resume_embedding.reshape(1, -1)
        similarities = Embedder.cosine_similarities(query, role_embeddings)

        results = []
        for idx, role_name in enumerate(cls._role_embeddings["names"]):
            semantic_score = float(similarities[idx])
            skill_info = cls._compute_skill_match_score(resume_skills, role_name)
            skill_score = skill_info["score"]

            role_data = cls._roles.get(role_name, {})
            dataset_stats = role_data.get("dataset_stats", {})
            rec_rate = dataset_stats.get("avg_recommendation_rate", 0.2)
            job_variants = dataset_stats.get("job_variants", 1)

            combined = (
                semantic_score * 0.40
                + skill_score * 0.45
                + rec_rate * 0.15
            )

            coverage_bonus = min(job_variants / 10.0, 0.05)
            combined += coverage_bonus

            results.append({
                "role": role_name,
                "score": round(combined * 100, 1),
                "semantic_similarity": round(semantic_score * 100, 1),
                "skill_match": round(skill_score * 100, 1),
                "matched_core_skills": skill_info["core_matched"],
                "matched_secondary_skills": skill_info["secondary_matched"],
                "description": role_data.get("description", ""),
                "core_skills": role_data.get("core_skills", []),
                "recommendation_rate": rec_rate,
                "job_variants": job_variants,
                "source": "heuristic",
            })

        results.sort(key=lambda x: x["score"], reverse=True)
        results = [r for r in results if r["score"] > 5.0]
        return results[:top_k]

    @classmethod
    def _skill_only_recommend(cls, resume_skills: set, top_k: int = 5) -> list[dict]:
        """Pure keyword-based fallback when embeddings are unavailable."""
        results = []
        for role_name, skill_sets in cls._role_skill_sets.items():
            core_match = resume_skills & skill_sets["core"]
            secondary_match = resume_skills & skill_sets["secondary"]
            core_count = len(core_match)
            secondary_count = len(secondary_match)
            max_possible = len(skill_sets["core"]) * 2 + len(skill_sets["secondary"])
            score = (core_count * 2 + secondary_count) / max_possible if max_possible > 0 else 0.0
            if score > 0:
                results.append({
                    "role": role_name,
                    "score": round(score * 100, 1),
                    "semantic_similarity": 0.0,
                    "skill_match": round(score * 100, 1),
                    "matched_core_skills": sorted(core_match),
                    "matched_secondary_skills": sorted(secondary_match),
                    "description": cls._roles.get(role_name, {}).get("description", ""),
                    "core_skills": cls._roles.get(role_name, {}).get("core_skills", []),
                    "recommendation_rate": 0.2,
                    "job_variants": 1,
                    "source": "skill_only",
                })
        results.sort(key=lambda x: x["score"], reverse=True)
        return results[:top_k]
