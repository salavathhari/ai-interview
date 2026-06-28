"""Skill extraction, gap analysis, and missing skills recommendation."""

from app.ml.models.skill_extractor import SkillExtractor
from app.ml.embeddings.embedder import Embedder
from app.ml.config import SKILL_SIMILARITY_THRESHOLD, SKILL_PARTIAL_THRESHOLD
import numpy as np


class SkillService:
    """High-level service for skill extraction and gap analysis."""

    @staticmethod
    def extract_skills(resume_text: str) -> dict:
        return SkillExtractor.extract_with_similarity(resume_text)

    @staticmethod
    def skill_gap(resume_text: str, jd_text: str) -> dict:
        resume_skills = SkillExtractor.extract(resume_text)
        resume_set = set(resume_skills.get("all_skills", []))

        jd_skills_data = SkillExtractor.extract(jd_text)
        jd_set = set(jd_skills_data.get("all_skills", []))

        if not jd_set:
            from app.ml.utils.text_preprocessor import TextPreprocessor
            import re
            text_lower = jd_text.lower()
            common_tech = [
                "Python", "JavaScript", "TypeScript", "React", "Node.js", "Express",
                "FastAPI", "Django", "Flask", "PostgreSQL", "MySQL", "MongoDB", "Redis",
                "Docker", "Kubernetes", "AWS", "Azure", "GCP", "Git", "Java", "C++",
                "CI/CD", "REST API", "GraphQL", "Terraform", "Ansible", "Jenkins",
                "Machine Learning", "Deep Learning", "NLP", "TensorFlow", "PyTorch",
            ]
            jd_set = set(s for s in common_tech if s.lower() in text_lower)

        matched = resume_set & jd_set
        missing = jd_set - resume_set

        partial = set()
        if missing:
            try:
                resume_embeddings = []
                resume_skills_list = list(resume_set) if resume_set else list(resume_skills.get("all_skills", []))
                if resume_skills_list:
                    resume_embeddings = Embedder.encode_batch(resume_skills_list)
                missing_list = list(missing)
                if missing_list and resume_embeddings.size > 0:
                    missing_embeddings = Embedder.encode_batch(missing_list)
                    for i, m_skill in enumerate(missing_list):
                        query = missing_embeddings[i].reshape(1, -1)
                        sims = Embedder.cosine_similarities(query, resume_embeddings)
                        max_sim = float(np.max(sims))
                        if max_sim >= SKILL_SIMILARITY_THRESHOLD:
                            matched.add(m_skill)
                            missing.discard(m_skill)
                        elif max_sim >= SKILL_PARTIAL_THRESHOLD:
                            partial.add(m_skill)
                            missing.discard(m_skill)
            except Exception:
                pass

        total = len(jd_set) if jd_set else 1
        match_pct = (len(matched) / total * 100) if total > 0 else 0

        return {
            "matched": sorted(matched),
            "partial": sorted(partial),
            "missing": sorted(missing),
            "match_percentage": round(match_pct, 1),
        }

    @staticmethod
    def recommend_skills(resume_text: str, target_role: str = "") -> dict:
        resume_skills = SkillExtractor.extract(resume_text)
        current_set = set(resume_skills.get("all_skills", []))

        try:
            # #17: Load job roles from the dataset JSON file directly
            import json
            from app.ml.config import JOB_ROLES_PATH
            with open(JOB_ROLES_PATH, "r") as f:
                roles_data = json.load(f)
        except Exception:
            roles_data = {}

        if target_role and target_role in roles_data:
            required = set(roles_data[target_role].get("core_skills", []))
        elif target_role:
            required = set()
            for role_name, role_data in roles_data.items():
                if target_role.lower() in role_name.lower() or role_name.lower() in target_role.lower():
                    required = set(role_data.get("core_skills", []))
                    break
        else:
            required = set()
            for role_data in roles_data.values():
                required.update(role_data.get("core_skills", []))

        missing = required - current_set
        recommended = sorted(missing)[:10]

        return {
            "current_skills": sorted(current_set),
            "recommended_skills": recommended,
            "target_role": target_role,
            "reasoning": f"Based on your resume and target role '{target_role or 'general'}', these skills would increase your employability.",
        }
