"""Feature extraction for ML models from resume text — enhanced with NER-derived knowledge."""

import json
import os
import re
from functools import lru_cache
from app.ml.utils.text_preprocessor import TextPreprocessor
from app.ml.config import ATS_KNOWLEDGE_PATH


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


class FeatureEngineer:
    """Extract numerical features from resume text for ML models.

    Uses NER-derived knowledge (skills, degrees, designations, experience patterns)
    from 220 annotated resumes for more accurate feature extraction.
    """

    ACTION_VERBS = [
        "achieved", "accelerated", "architected", "automated", "built",
        "collaborated", "configured", "created", "delivered", "deployed",
        "designed", "developed", "drove", "eliminated", "engineered",
        "established", "executed", "expanded", "generated", "grew",
        "implemented", "improved", "increased", "initiated", "integrated",
        "introduced", "launched", "led", "maintained", "managed",
        "migrated", "modernized", "negotiated", "optimized", "orchestrated",
        "overhauled", "pioneered", "planned", "produced", "programmed",
        "reduced", "refactored", "redesigned", "revamped", "scaled",
        "simplified", "solved", "standardized", "strengthened", "streamlined",
        "supervised", "transformed", "troubleshooted",
    ]

    EDUCATION_LEVELS = {
        "high school": 1, "diploma": 1,
        "associate": 2, "bachelor": 3, "b.tech": 3, "b.sc": 3, "b.e.": 3,
        "bca": 3, "be ": 3,
        "master": 4, "m.tech": 4, "m.sc": 4, "mba": 4, "m.e.": 4, "mca": 4,
        "phd": 5, "doctorate": 5, "ph.d": 5,
    }

    @staticmethod
    def _get_dataset_skills() -> set:
        kb = _get_ats_kb()
        skills = set()
        for category in kb.get("skills", {}).values():
            for item in category:
                skills.add(item["name"].lower())
        return skills

    @staticmethod
    def _get_dataset_designations() -> list[str]:
        kb = _get_ats_kb()
        return [d["name"] for d in kb.get("designations", [])]

    @staticmethod
    def extract_all_features(resume_text: str, jd_text: str = "") -> dict:
        preprocessor = TextPreprocessor()
        sections = preprocessor.extract_sections(resume_text)
        text_lower = resume_text.lower()

        word_count = preprocessor.word_count(resume_text)
        section_names = list(sections.keys())
        section_count = len(section_names)

        experience_years = FeatureEngineer._extract_experience_years(text_lower)
        education_level = FeatureEngineer._extract_education_level(text_lower)
        project_count = FeatureEngineer._extract_project_count(text_lower, sections)
        certification_count = FeatureEngineer._extract_certification_count(text_lower, sections)
        action_verb_count = FeatureEngineer._count_action_verbs(text_lower)
        action_verb_density = action_verb_count / max(word_count, 1)
        section_completeness = preprocessor.section_completeness(resume_text)

        keyword_density = 0.0
        if jd_text:
            keyword_density = FeatureEngineer._keyword_density(resume_text, jd_text)

        # Enhanced skill extraction using NER-derived knowledge
        skill_count = FeatureEngineer._extract_skill_count(text_lower)

        # New features from NER dataset
        has_contact = FeatureEngineer._has_contact_info(text_lower)
        has_experience_section = 1.0 if "experience" in sections or "work history" in sections or "employment" in sections else 0.0
        has_education_section = 1.0 if "education" in sections else 0.0
        has_skills_section = 1.0 if "skills" in sections or "technical skills" in sections else 0.0
        designation_count = FeatureEngineer._extract_designation_count(text_lower)
        company_count = FeatureEngineer._extract_company_count(text_lower)

        return {
            "resume_length": word_count,
            "section_count": section_count,
            "skill_count": skill_count,
            "experience_years": experience_years,
            "project_count": project_count,
            "education_level": education_level,
            "certification_count": certification_count,
            "keyword_density": keyword_density,
            "section_completeness": section_completeness,
            "action_verb_density": action_verb_density,
            "has_contact_info": has_contact,
            "has_experience_section": has_experience_section,
            "has_education_section": has_education_section,
            "has_skills_section": has_skills_section,
            "designation_count": designation_count,
            "company_count": company_count,
            "resume_text": resume_text,
        }

    @staticmethod
    def get_feature_vector(features: dict) -> list[float]:
        return [
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
            float(features.get("has_contact_info", 0)),
            float(features.get("has_experience_section", 0)),
            float(features.get("has_education_section", 0)),
            float(features.get("has_skills_section", 0)),
            float(features.get("designation_count", 0)),
            float(features.get("company_count", 0)),
        ]

    @staticmethod
    def _extract_experience_years(text: str) -> int:
        # Try explicit experience statements first
        patterns = [
            r"(\d{1,2})\+?\s*years?\s*(?:of)?\s*(?:experience|exp)",
            r"experience[:\s]*(\d{1,2})\+?\s*years?",
            r"(\d{1,2})\+?\s*years?\s*(?:in|with|of)",
            r"total\s*(?:experience|exp)[:\s]*(\d{1,2})",
            r"(\d{1,2})\+?\s*years?\s*(?:professional|work)",
        ]
        for pattern in patterns:
            match = re.search(pattern, text)
            if match:
                years = int(match.group(1))
                if 0 < years <= 50:
                    return years

        # Try NER-style "X years" patterns
        ner_patterns = [
            r"(\d+\.?\d*)\s*years?(?:\s*of)?\s*(?:experience|work|professional)",
            r"(?:experience|exp)[:\s]*(\d+\.?\d*)\s*years?",
        ]
        for pattern in ner_patterns:
            match = re.search(pattern, text)
            if match:
                years = float(match.group(1))
                if 0 < years <= 50:
                    return int(years)

        # Fallback: count date ranges
        date_ranges = re.findall(
            r"(?:20[0-2]\d|19\d\d)\s*[-–]\s*(?:20[0-2]\d|19\d\d|present|current|now)",
            text,
        )
        return max(0, len(date_ranges) - 1) if date_ranges else 0

    @staticmethod
    def _extract_education_level(text: str) -> int:
        # Check dataset-informed education keywords first
        kb = _get_ats_kb()
        ed_keywords = kb.get("education_keywords", [])
        for keyword in ed_keywords:
            if keyword in text:
                # Map to level
                for kw, level in sorted(FeatureEngineer.EDUCATION_LEVELS.items(), key=lambda x: -x[1]):
                    if kw in keyword:
                        return level

        # Fall back to original detection
        for keyword, level in sorted(FeatureEngineer.EDUCATION_LEVELS.items(), key=lambda x: -x[1]):
            if keyword in text:
                return level
        return 0

    @staticmethod
    def _extract_skill_count(text: str) -> int:
        """Count skills using NER-derived skill dictionary + regex fallback."""
        dataset_skills = FeatureEngineer._get_dataset_skills()
        count = 0
        for skill in dataset_skills:
            if len(skill) > 2 and skill in text:
                count += 1

        if count == 0:
            # Fallback to regex
            count = len(re.findall(
                r"\b(python|java|javascript|typescript|react|angular|vue|node|express|"
                r"fastapi|django|flask|spring|sql|mysql|postgresql|mongodb|redis|"
                r"docker|kubernetes|aws|azure|gcp|git|ci/cd|terraform|ansible|"
                r"tensorflow|pytorch|scikit|pandas|numpy|machine learning|"
                r"deep learning|nlp|computer vision|rest|graphql|microservices|"
                r"linux|agile|scrum|jira|figma|sketch|html|css|sass|swift|"
                r"kotlin|ruby|php|go|rust|scala|r lang|bash|powershell)\b",
                text
            ))
        return count

    @staticmethod
    def _has_contact_info(text: str) -> float:
        score = 0.0
        if re.search(r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}", text):
            score += 0.3
        if re.search(r"\b\d{10,}\b", text):
            score += 0.3
        if re.search(r"linkedin|github|portfolio|indeed", text):
            score += 0.2
        if re.search(r"\b[A-Z][a-z]+(?:,\s*[A-Z][a-z]+)+\b", text):
            score += 0.2
        return min(score, 1.0)

    @staticmethod
    def _extract_designation_count(text: str) -> int:
        designations = FeatureEngineer._get_dataset_designations()
        count = 0
        for des in designations:
            if des.lower() in text:
                count += 1
        return count

    @staticmethod
    def _extract_company_count(text: str) -> int:
        kb = _get_ats_kb()
        companies = [c["name"].lower() for c in kb.get("companies", [])]
        count = 0
        for comp in companies:
            if comp in text:
                count += 1
        return count

    @staticmethod
    def _extract_project_count(text: str, sections: dict) -> int:
        project_section = sections.get("projects", "")
        if project_section:
            bullets = re.findall(r"[•\-\*]\s+", project_section)
            if bullets:
                return len(bullets)
            subheadings = re.findall(r"(?:^|\n)[A-Z][\w\s]+(?:–\-:|:)", project_section)
            if subheadings:
                return len(subheadings)
        project_keywords = re.findall(r"\bproject\b", text)
        return min(len(project_keywords), 20)

    @staticmethod
    def _extract_certification_count(text: str, sections: dict) -> int:
        cert_section = sections.get("certifications", "") or sections.get("awards", "")
        if cert_section:
            items = re.findall(r"[•\-\*]\s+|\n(?=[A-Z])", cert_section)
            return max(len(items), 1) if cert_section.strip() else 0
        cert_keywords = [
            "certified", "certification", "certificate", "aws certified",
            "google certified", "microsoft certified", "oracle certified",
            "pmp", "ci/cd", "ckad", "cka",
        ]
        return sum(1 for kw in cert_keywords if kw in text.lower())

    @staticmethod
    def _count_action_verbs(text: str) -> int:
        return sum(1 for verb in FeatureEngineer.ACTION_VERBS if verb in text)

    @staticmethod
    def _keyword_density(resume_text: str, jd_text: str) -> float:
        jd_words = set(re.findall(r"[a-zA-Z]{3,}", jd_text.lower()))
        jd_words -= {"the", "and", "for", "with", "this", "that", "are", "was", "have", "has"}
        if not jd_words:
            return 0.0
        resume_words = set(re.findall(r"[a-zA-Z]{3,}", resume_text.lower()))
        overlap = jd_words & resume_words
        return len(overlap) / len(jd_words) if jd_words else 0.0
