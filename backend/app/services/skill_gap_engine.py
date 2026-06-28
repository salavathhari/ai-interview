"""
SkillGapEngine — Full intelligence pipeline.

Orchestrates resume analysis, JD analysis, interview performance,
and coding performance into a unified skill assessment with
dependency mapping, priority classification, and learning roadmap.
"""

import json
import time
from collections import OrderedDict
from typing import Dict, List, Optional, Any
from datetime import datetime, timezone
from sqlalchemy.orm import Session

from app.models.career import (
    JobDescription, ResumeAnalysis, SkillGapAnalysis, LearningRoadmap
)
from app.models.interview_session import InterviewSession
from app.models.coding_challenge import CodingSession, CodingSubmission, CodingChallenge
from app.models.intelligence import (
    PerformanceMetrics, SkillAnalytics, CareerRecommendation, LearningProgress
)
from app.services.skill_dependency_mapper import SkillDependencyMapper


SKILL_NORM = {
    "node": "node.js", "nodejs": "node.js", "node js": "node.js",
    "react.js": "react", "reactjs": "react", "react js": "react",
    "vue.js": "vue", "vuejs": "vue", "vue js": "vue",
    "angular.js": "angular", "angularjs": "angular",
    "next.js": "nextjs", "next js": "nextjs",
    "express.js": "express", "expressjs": "express",
    "ts": "typescript", "js": "javascript", "py": "python",
    "postgres": "postgresql", "k8s": "kubernetes", "tf": "terraform",
    "ci/cd": "ci_cd", "rest api": "rest_api", "rest": "rest_api",
    "object oriented programming": "oop", "object-oriented programming": "oop",
    "ml": "machine_learning", "ds&a": "dsa",
    "data structures and algorithms": "dsa", "data structures & algorithms": "dsa",
    "amazon web services": "aws", "google cloud platform": "gcp",
    "google cloud": "gcp", "microsoft azure": "azure",
}


def _normalize_skill(skill: str) -> str:
    s = skill.lower().strip()
    return SKILL_NORM.get(s, s)


class _AnalysisCache:
    """Simple LRU cache for analysis results (avoids re-computation)."""
    def __init__(self, maxsize: int = 128, ttl: int = 300):
        self._cache: OrderedDict = OrderedDict()
        self._maxsize = maxsize
        self._ttl = ttl
        self._lock = __import__("threading").Lock()

    def get(self, key: str) -> Optional[Dict]:
        with self._lock:
            if key in self._cache:
                entry = self._cache[key]
                if time.time() - entry["ts"] < self._ttl:
                    self._cache.move_to_end(key)
                    return entry["data"]
                del self._cache[key]
            return None

    def set(self, key: str, data: Dict):
        with self._lock:
            if key in self._cache:
                del self._cache[key]
            elif len(self._cache) >= self._maxsize:
                self._cache.popitem(last=False)
            self._cache[key] = {"data": data, "ts": time.time()}

    def invalidate_user(self, user_id: int):
        prefix = f"user:{user_id}:"
        with self._lock:
            keys_to_delete = [k for k in self._cache if k.startswith(prefix)]
            for k in keys_to_delete:
                del self._cache[k]


_analysis_cache = _AnalysisCache()


# Skill categories for classification
SKILL_CATEGORIES = {
    "programming": [
        "python", "java", "javascript", "typescript", "c++", "c", "go", "rust",
        "kotlin", "swift", "ruby", "php", "scala", "r", "matlab", "sql"
    ],
    "frontend": [
        "html", "css", "react", "vue", "angular", "nextjs", "tailwindcss",
        "sass", "bootstrap", "jquery", "webpack", "vite"
    ],
    "backend": [
        "fastapi", "django", "flask", "spring", "express", "nodejs",
        "rest_api", "graphql", "grpc"
    ],
    "database": [
        "mysql", "postgresql", "sqlite", "mongodb", "redis", "elasticsearch",
        "cassandra", "dynamodb", "firebase"
    ],
    "cloud": [
        "aws", "gcp", "azure", "aws_ec2", "aws_s3", "aws_lambda", "aws_rds",
        "docker", "kubernetes", "terraform", "ci_cd"
    ],
    "devops": [
        "git", "linux", "bash", "docker", "docker_compose", "kubernetes",
        "jenkins", "github_actions", "nginx", "ci_cd"
    ],
    "data_ml": [
        "pandas", "numpy", "scikit_learn", "tensorflow", "pytorch",
        "machine_learning", "deep_learning", "nlp", "computer_vision",
        "data_pipeline", "apache_spark", "kafka", "tableau"
    ],
    "cs_fundamentals": [
        "data_structures", "algorithms", "dsa", "object_oriented_programming",
        "operating_systems", "computer_networks", "database_management",
        "design_patterns", "compiler_design"
    ],
    "system_design": [
        "system_design_basics", "distributed_systems", "microservices",
        "message_queues", "caching", "load_balancing", "api_design"
    ],
    "testing": [
        "unit_testing", "integration_testing", "pytest", "jest",
        "selenium", "cypress", "tdd"
    ],
    "soft_skills": [
        "communication", "teamwork", "leadership", "problem_solving",
        "time_management", "presentation", "critical_thinking"
    ],
}

# Interview topic to skill mapping
INTERVIEW_SKILL_MAP = {
    "score_dsa": ["data_structures", "algorithms", "dsa"],
    "score_dbms": ["sql", "database_management", "mysql", "postgresql"],
    "score_os": ["operating_systems", "linux"],
    "score_cn": ["computer_networks"],
    "score_oop": ["object_oriented_programming", "design_patterns"],
    "score_system_design": ["system_design_basics", "distributed_systems", "microservices"],
    "score_project": [],  # Project-specific, no fixed skills
    "score_hr": ["communication", "teamwork", "leadership"],
    "score_communication": ["communication", "presentation"],
}

# Coding topic to skill mapping
CODING_SKILL_MAP = {
    "arrays": ["data_structures", "algorithms"],
    "strings": ["data_structures", "algorithms"],
    "hashmap": ["data_structures"],
    "linked_list": ["data_structures"],
    "stack": ["data_structures"],
    "queue": ["data_structures"],
    "tree": ["data_structures", "algorithms"],
    "graph": ["data_structures", "algorithms"],
    "dynamic_programming": ["algorithms", "dsa"],
    "sorting": ["algorithms"],
    "searching": ["algorithms"],
    "recursion": ["algorithms"],
    "sql": ["sql", "database_management"],
    "greedy": ["algorithms"],
    "bit_manipulation": ["algorithms"],
    "math": ["statistics"],
    "backtracking": ["algorithms"],
    "heap": ["data_structures"],
    "trie": ["data_structures"],
    "union_find": ["data_structures"],
}


class SkillGapEngine:
    """
    Full intelligence pipeline that:
    1. Aggregates data from resume, JD, interview, and coding
    2. Classifies skills with priority and reasoning
    3. Maps learning dependencies
    4. Generates personalized learning roadmap
    5. Produces career recommendations
    """

    def __init__(self, db: Session):
        self.db = db
        self.dep_mapper = SkillDependencyMapper()

    def analyze(
        self,
        user_id: int,
        resume_analysis_id: Optional[int] = None,
        job_description_id: Optional[int] = None,
        force_refresh: bool = False,
    ) -> Dict[str, Any]:
        """
        Run full skill gap analysis pipeline.
        Returns comprehensive skill assessment.
        Uses in-memory cache (5min TTL) to avoid re-computation.
        """
        # Check cache first
        cache_key = f"user:{user_id}:resume:{resume_analysis_id}:jd:{job_description_id}"
        if not force_refresh:
            cached = _analysis_cache.get(cache_key)
            if cached is not None:
                return cached
        # 1. Gather all data sources
        resume_data = self._get_resume_data(user_id, resume_analysis_id)
        jd_data = self._get_jd_data(user_id, job_description_id)
        interview_data = self._get_interview_performance(user_id)
        coding_data = self._get_coding_performance(user_id)
        learning_data = self._get_learning_progress(user_id)

        # 2. Extract skills from each source
        resume_skills = self._extract_skills_from_resume(resume_data)
        jd_required = self._extract_skills_from_jd(jd_data)
        jd_preferred = self._extract_preferred_skills(jd_data)
        interview_weak = self._extract_weak_skills(interview_data)
        interview_strong = self._extract_strong_skills(interview_data)
        coding_weak = self._extract_coding_weak_skills(coding_data)
        coding_strong = self._extract_coding_strong_skills(coding_data)

        # 3. Unified skill classification
        all_required = list(set(jd_required + jd_preferred))
        all_existing = list(set(resume_skills + interview_strong + coding_strong))
        all_weak = list(set(interview_weak + coding_weak))

        skill_assessment = self._classify_skills(
            existing_skills=all_existing,
            required_skills=all_required,
            weak_skills=all_weak,
            jd_data=jd_data,
            interview_data=interview_data,
            coding_data=coding_data,
            learning_data=learning_data,
        )

        # 4. Compute match percentage (required + preferred)
        all_jd_skills = list(set(jd_required + jd_preferred))
        if all_jd_skills:
            normalized_existing = set(_normalize_skill(s) for s in resume_skills)
            normalized_jd = set(_normalize_skill(s) for s in all_jd_skills)
            matched_count = len(normalized_existing & normalized_jd)
            match_percentage = round((matched_count / len(normalized_jd)) * 100, 1)
        else:
            match_percentage = None

        # 5. Generate learning path with dependencies
        missing_skills = skill_assessment["missing"]
        learning_path = self.dep_mapper.get_learning_path(
            [s["skill"] for s in missing_skills]
        )

        # 6. Generate recommendations
        recommendations = self._generate_recommendations(
            skill_assessment, interview_data, coding_data, learning_data
        )

        # 7. Build final result
        total_estimated_hours = sum(
            s.get("estimated_hours", 0) for s in skill_assessment["missing"]
        )

        result = {
            "match_percentage": match_percentage,
            "existing_skills": skill_assessment["existing"],
            "missing_skills": skill_assessment["missing"],
            "weak_skills": skill_assessment["weak"],
            "strong_skills": skill_assessment["strong"],
            "unused_skills": skill_assessment["unused"],
            "transferable_skills": skill_assessment["transferable"],
            "learning_skills": skill_assessment.get("learning", []),
            "learning_path": learning_path,
            "recommendations": recommendations,
            "interview_summary": interview_data,
            "coding_summary": coding_data,
            "learning_summary": learning_data,
            "total_estimated_hours": round(total_estimated_hours, 1),
            "analyzed_at": datetime.now(timezone.utc).isoformat(),
        }

        # Cache the result
        _analysis_cache.set(cache_key, result)

        return result

    # ── Data Gathering ──

    def _get_resume_data(self, user_id: int, resume_analysis_id: Optional[int]) -> Optional[Dict]:
        if resume_analysis_id:
            analysis = self.db.query(ResumeAnalysis).filter(
                ResumeAnalysis.id == resume_analysis_id
            ).first()
        else:
            analysis = self.db.query(ResumeAnalysis).filter(
                ResumeAnalysis.user_id == user_id
            ).order_by(ResumeAnalysis.created_at.desc()).first()

        if not analysis:
            return None

        return {
            "id": analysis.id,
            "detected_skills": self._parse_json(analysis.detected_skills),
            "technologies": self._parse_json(analysis.technologies),
            "projects": self._parse_json(analysis.projects),
            "experience_level": analysis.experience_level,
            "education": self._parse_json(analysis.education),
            "certifications": self._parse_json(analysis.certifications),
        }

    def _get_jd_data(self, user_id: int, job_description_id: Optional[int]) -> Optional[Dict]:
        if job_description_id:
            jd = self.db.query(JobDescription).filter(
                JobDescription.id == job_description_id
            ).first()
        else:
            jd = self.db.query(JobDescription).filter(
                JobDescription.user_id == user_id
            ).order_by(JobDescription.created_at.desc()).first()

        if not jd:
            return None

        return {
            "id": jd.id,
            "title": jd.title,
            "company": jd.company,
            "required_skills": self._parse_json(jd.required_skills),
            "preferred_skills": self._parse_json(jd.preferred_skills),
            "technologies": self._parse_json(jd.technologies),
            "responsibilities": self._parse_json(jd.responsibilities),
            "experience_years": jd.experience_years,
            "education": self._parse_json(jd.education_requirements) if jd.education_requirements else [],
            "soft_skills": self._parse_json(jd.soft_skills),
            "keywords": self._parse_json(jd.keywords),
        }

    def _get_interview_performance(self, user_id: int) -> Optional[Dict]:
        session = self.db.query(InterviewSession).filter(
            InterviewSession.user_id == user_id,
            InterviewSession.status == "completed",
        ).order_by(InterviewSession.ended_at.desc()).first()

        if not session:
            return None

        topic_scores = {}
        for field, name in [
            ("score_dsa", "dsa"), ("score_dbms", "dbms"),
            ("score_os", "os"), ("score_cn", "computer_networks"),
            ("score_oop", "oop"), ("score_system_design", "system_design"),
            ("score_hr", "hr"), ("score_communication", "communication"),
        ]:
            val = getattr(session, field, None)
            if val is not None:
                topic_scores[name] = val

        weak_topics = [t for t, s in topic_scores.items() if s < 60]
        strong_topics = [t for t, s in topic_scores.items() if s >= 75]

        return {
            "id": session.id,
            "overall_score": session.score,
            "topic_scores": topic_scores,
            "weak_topics": weak_topics,
            "strong_topics": strong_topics,
            "role": session.role,
            "difficulty": session.difficulty,
        }

    def _get_coding_performance(self, user_id: int) -> Optional[Dict]:
        sessions = self.db.query(CodingSession).filter(
            CodingSession.user_id == user_id,
            CodingSession.status == "submitted",
        ).order_by(CodingSession.ended_at.desc()).limit(20).all()

        if not sessions:
            return None

        topic_scores = {}
        for cs in sessions:
            if cs.challenge and cs.challenge.topics:
                for topic in cs.challenge.topics:
                    if topic not in topic_scores:
                        topic_scores[topic] = []
                    topic_scores[topic].append(cs.coding_score or 0)

        # Average scores per topic
        avg_scores = {
            t: round(sum(scores) / len(scores), 1)
            for t, scores in topic_scores.items()
        }

        weak_topics = [t for t, s in avg_scores.items() if s < 60]
        strong_topics = [t for t, s in avg_scores.items() if s >= 75]

        overall = sum(cs.coding_score or 0 for cs in sessions) / len(sessions)

        return {
            "overall_score": round(overall, 1),
            "topic_scores": avg_scores,
            "weak_topics": weak_topics,
            "strong_topics": strong_topics,
            "total_sessions": len(sessions),
        }

    def _get_learning_progress(self, user_id: int) -> Optional[Dict]:
        progress = self.db.query(LearningProgress).filter(
            LearningProgress.user_id == user_id
        ).all()

        if not progress:
            return None

        completed = [p.topic_name for p in progress if p.status in ("completed", "mastered")]
        in_progress = [p.topic_name for p in progress if p.status == "in_progress"]
        total_hours = sum(p.actual_hours or 0 for p in progress)

        return {
            "completed_topics": completed,
            "in_progress_topics": in_progress,
            "total_hours_learned": round(total_hours, 1),
            "topics_completed": len(completed),
        }

    # ── Skill Extraction ──

    def _extract_skills_from_resume(self, resume_data: Optional[Dict]) -> List[str]:
        if not resume_data:
            return []

        skills = set()
        for skill_list_field in ["detected_skills", "technologies"]:
            items = resume_data.get(skill_list_field, [])
            if isinstance(items, list):
                for item in items:
                    if isinstance(item, str):
                        normalized = _normalize_skill(item.lower().strip())
                        skills.add(normalized)
                    elif isinstance(item, dict):
                        name = item.get("name") or item.get("skill") or item.get("tool", "")
                        if name:
                            normalized = _normalize_skill(name.lower().strip())
                            skills.add(normalized)

        # Extract from projects
        for project in resume_data.get("projects", []):
            if isinstance(project, dict):
                tech = project.get("technologies", [])
                if isinstance(tech, list):
                    for t in tech:
                        if isinstance(t, str):
                            normalized = _normalize_skill(t.lower().strip())
                            skills.add(normalized)

        return list(skills)

    def _extract_skills_from_jd(self, jd_data: Optional[Dict]) -> List[str]:
        if not jd_data:
            return []

        skills = set()
        for field in ["required_skills", "technologies"]:
            items = jd_data.get(field, [])
            if isinstance(items, list):
                for item in items:
                    if isinstance(item, str):
                        normalized = _normalize_skill(item.lower().strip())
                        skills.add(normalized)
                    elif isinstance(item, dict):
                        name = item.get("name") or item.get("skill") or item.get("technology", "")
                        if name:
                            normalized = _normalize_skill(name.lower().strip())
                            skills.add(normalized)

        return list(skills)

    def _extract_preferred_skills(self, jd_data: Optional[Dict]) -> List[str]:
        if not jd_data:
            return []

        skills = set()
        items = jd_data.get("preferred_skills", [])
        if isinstance(items, list):
            for item in items:
                if isinstance(item, str):
                    normalized = _normalize_skill(item.lower().strip())
                    skills.add(normalized)
                elif isinstance(item, dict):
                    name = item.get("name") or item.get("skill", "")
                    if name:
                        normalized = _normalize_skill(name.lower().strip())
                        skills.add(normalized)
        return list(skills)

    def _extract_weak_skills(self, interview_data: Optional[Dict]) -> List[str]:
        if not interview_data:
            return []

        skills = set()
        for topic in interview_data.get("weak_topics", []):
            mapped = INTERVIEW_SKILL_MAP.get(f"score_{topic}", [])
            skills.update(mapped)
        return list(skills)

    def _extract_strong_skills(self, interview_data: Optional[Dict]) -> List[str]:
        if not interview_data:
            return []

        skills = set()
        for topic in interview_data.get("strong_topics", []):
            mapped = INTERVIEW_SKILL_MAP.get(f"score_{topic}", [])
            skills.update(mapped)
        return list(skills)

    def _extract_coding_weak_skills(self, coding_data: Optional[Dict]) -> List[str]:
        if not coding_data:
            return []

        skills = set()
        for topic in coding_data.get("weak_topics", []):
            mapped = CODING_SKILL_MAP.get(topic, [])
            skills.update(mapped)
        return list(skills)

    def _extract_coding_strong_skills(self, coding_data: Optional[Dict]) -> List[str]:
        if not coding_data:
            return []

        skills = set()
        for topic in coding_data.get("strong_topics", []):
            mapped = CODING_SKILL_MAP.get(topic, [])
            skills.update(mapped)
        return list(skills)

    # ── Skill Classification ──

    def _classify_skills(
        self,
        existing_skills: List[str],
        required_skills: List[str],
        weak_skills: List[str],
        jd_data: Optional[Dict],
        interview_data: Optional[Dict],
        coding_data: Optional[Dict],
        learning_data: Optional[Dict] = None,
    ) -> Dict[str, List[Dict]]:
        """Classify all skills into categories with reasoning."""

        existing_set = set(_normalize_skill(s) for s in existing_skills)
        required_set = set(_normalize_skill(s) for s in required_skills)
        weak_set = set(_normalize_skill(s) for s in weak_skills)

        # Determine which required are truly mandatory vs preferred
        mandatory_set = set()
        preferred_set = set()
        if jd_data:
            for skill in jd_data.get("required_skills", []):
                name = skill if isinstance(skill, str) else skill.get("name", "")
                mandatory_set.add(_normalize_skill(name.lower()))
            for skill in jd_data.get("preferred_skills", []):
                name = skill if isinstance(skill, str) else skill.get("name", "")
                preferred_set.add(_normalize_skill(name.lower()))

        classified = {
            "existing": [],
            "missing": [],
            "weak": [],
            "strong": [],
            "unused": [],
            "transferable": [],
            "learning": [],
        }

        # Learning skills (topics currently being learned)
        learning_set = set()
        if learning_data:
            for topic in learning_data.get("in_progress_topics", []):
                learning_set.add(_normalize_skill(topic))
            for topic in learning_data.get("completed_topics", []):
                learning_set.add(_normalize_skill(topic))

        # Existing skills
        for skill in existing_set:
            reason = self._get_skill_reason(skill, "existing", jd_data, interview_data, coding_data)
            priority = "high" if skill in mandatory_set else "medium" if skill in preferred_set else "low"
            classified["existing"].append({
                "skill": skill,
                "priority": priority,
                "reason": reason,
                "source": self._get_skill_source(skill, existing_skills, interview_data, coding_data),
            })

        # Missing skills (required but not in existing)
        for skill in required_set - existing_set:
            priority = "critical" if skill in mandatory_set else "high" if skill in preferred_set else "medium"
            reason = self._get_skill_reason(skill, "missing", jd_data, interview_data, coding_data)
            estimated_hours = self._estimate_learning_hours(skill)
            classified["missing"].append({
                "skill": skill,
                "priority": priority,
                "reason": reason,
                "interview_score": self._get_interview_score_for_skill(skill, interview_data),
                "resume_present": skill in existing_set,
                "estimated_hours": estimated_hours,
            })

        # Weak skills (low performance in interview/coding)
        for skill in weak_set:
            if skill in existing_set:
                reason = self._get_skill_reason(skill, "weak", jd_data, interview_data, coding_data)
                score = self._get_interview_score_for_skill(skill, interview_data)
                classified["weak"].append({
                    "skill": skill,
                    "priority": "high",
                    "reason": reason,
                    "current_score": score,
                })

        # Strong skills (high performance)
        for skill in existing_set:
            if skill not in weak_set and self._is_strong_skill(skill, interview_data, coding_data):
                reason = self._get_skill_reason(skill, "strong", jd_data, interview_data, coding_data)
                classified["strong"].append({
                    "skill": skill,
                    "reason": reason,
                })

        # Unused skills (in resume but not required by JD)
        for skill in existing_set:
            if skill not in required_set and skill not in weak_set:
                classified["unused"].append({
                    "skill": skill,
                    "reason": f"{skill} is on your resume but not required by the target role",
                })

        # Transferable skills (from adjacent domains)
        for skill in existing_set:
            category = self._get_skill_category(skill)
            if category and skill not in required_set:
                adjacent_required = [
                    s for s in required_set
                    if self._get_skill_category(s) == category
                ]
                if adjacent_required:
                    classified["transferable"].append({
                        "skill": skill,
                        "related_to": adjacent_required,
                        "reason": f"{skill} transfers to {', '.join(adjacent_required)} in the same category ({category})",
                    })

        # Learning skills (in progress or completed via learning roadmap)
        for skill in learning_set:
            if skill in required_set and skill not in existing_set:
                classified["learning"].append({
                    "skill": skill,
                    "reason": f"Currently learning {skill}",
                    "priority": "medium",
                })

        return classified

    def _estimate_learning_hours(self, skill: str) -> float:
        """Estimate hours to learn a skill based on dependencies and category."""
        difficulty_hours = {
            "programming": 120,
            "frontend": 80,
            "backend": 100,
            "database": 60,
            "cloud": 90,
            "devops": 80,
            "data_ml": 150,
            "cs_fundamentals": 100,
            "system_design": 120,
            "testing": 50,
            "soft_skills": 40,
        }
        category = self._get_skill_category(skill)
        base_hours = difficulty_hours.get(category, 80)

        # Add hours for unmet dependencies
        prereqs = self.dep_mapper.get_all_prerequisites(skill)
        dep_hours = sum(self._estimate_learning_hours(p) for p in prereqs) * 0.3

        return round(base_hours + dep_hours, 1)

    def _get_skill_reason(
        self, skill: str, status: str, jd_data, interview_data, coding_data
    ) -> str:
        reasons = []
        if jd_data:
            required = [s.lower() for s in (jd_data.get("required_skills", []) or [])]
            preferred = [s.lower() for s in (jd_data.get("preferred_skills", []) or [])]
            if skill in required:
                reasons.append(f"Required by {jd_data.get('title', 'the job description')}")
            elif skill in preferred:
                reasons.append("Preferred by employer")

        if interview_data and status in ("weak", "missing"):
            topic_score = self._get_interview_score_for_skill(skill, interview_data)
            if topic_score is not None and topic_score < 60:
                reasons.append(f"Interview score: {topic_score}%")

        if coding_data and status in ("weak", "missing"):
            for topic, score in coding_data.get("topic_scores", {}).items():
                mapped = CODING_SKILL_MAP.get(topic, [])
                if skill in mapped and score < 60:
                    reasons.append(f"Coding performance: {score}% in {topic}")

        if not reasons:
            if status == "existing":
                reasons.append("Found in your resume")
            elif status == "missing":
                reasons.append("Not found in your skills")
            elif status == "weak":
                reasons.append("Below proficiency threshold")
            elif status == "strong":
                reasons.append("Above proficiency threshold")
            elif status == "learning":
                reasons.append("Currently being learned")

        return "; ".join(reasons) if reasons else f"Skill: {skill}"

    def _get_skill_source(
        self, skill: str, existing_skills, interview_data, coding_data
    ) -> str:
        sources = []
        if skill in [s.lower() for s in existing_skills]:
            sources.append("resume")
        if interview_data:
            for topic in interview_data.get("strong_topics", []):
                mapped = INTERVIEW_SKILL_MAP.get(f"score_{topic}", [])
                if skill in mapped:
                    sources.append("interview")
        if coding_data:
            for topic in coding_data.get("strong_topics", []):
                mapped = CODING_SKILL_MAP.get(topic, [])
                if skill in mapped:
                    sources.append("coding")
        return ", ".join(sources) if sources else "resume"

    def _get_interview_score_for_skill(self, skill: str, interview_data: Optional[Dict]) -> Optional[float]:
        if not interview_data:
            return None
        for topic, score in interview_data.get("topic_scores", {}).items():
            mapped = INTERVIEW_SKILL_MAP.get(f"score_{topic}", [])
            if skill in mapped:
                return score
        return None

    def _is_strong_skill(self, skill: str, interview_data, coding_data) -> bool:
        if interview_data:
            for topic in interview_data.get("strong_topics", []):
                mapped = INTERVIEW_SKILL_MAP.get(f"score_{topic}", [])
                if skill in mapped:
                    return True
        if coding_data:
            for topic in coding_data.get("strong_topics", []):
                mapped = CODING_SKILL_MAP.get(topic, [])
                if skill in mapped:
                    return True
        return False

    def _get_skill_category(self, skill: str) -> Optional[str]:
        for category, skills in SKILL_CATEGORIES.items():
            if skill in skills:
                return category
        return None

    # ── Recommendations ──

    def _generate_recommendations(
        self, skill_assessment, interview_data, coding_data, learning_data
    ) -> List[Dict]:
        """Generate prioritized career recommendations."""
        recs = []

        # Skill-based recommendations
        missing_critical = [s for s in skill_assessment["missing"] if s["priority"] == "critical"]
        if missing_critical:
            names = [s["skill"] for s in missing_critical[:3]]
            recs.append({
                "type": "skill",
                "title": "Learn Critical Missing Skills",
                "description": f"Focus on: {', '.join(names)}",
                "priority": "critical",
                "action": "Generate a learning roadmap targeting these skills",
            })

        # Interview recommendations
        if interview_data and interview_data.get("overall_score", 100) < 70:
            weak = interview_data.get("weak_topics", [])
            if weak:
                recs.append({
                    "type": "interview",
                    "title": "Improve Interview Performance",
                    "description": f"Weak areas: {', '.join(weak[:3])}",
                    "priority": "high",
                    "action": "Practice interview questions on these topics",
                })

        # Coding recommendations
        if coding_data and coding_data.get("overall_score", 100) < 70:
            weak = coding_data.get("weak_topics", [])
            if weak:
                recs.append({
                    "type": "coding",
                    "title": "Strengthen Coding Skills",
                    "description": f"Weak areas: {', '.join(weak[:3])}",
                    "priority": "high",
                    "action": "Solve practice problems on these topics",
                })

        # Learning progress recommendations
        if learning_data:
            in_progress = learning_data.get("in_progress_topics", [])
            if in_progress:
                recs.append({
                    "type": "learning",
                    "title": "Continue Learning",
                    "description": f"You have {len(in_progress)} topics in progress",
                    "priority": "medium",
                    "action": "Complete your current learning topics",
                })

        # Strong skills - leverage them
        if skill_assessment["strong"]:
            names = [s["skill"] for s in skill_assessment["strong"][:3]]
            recs.append({
                "type": "career",
                "title": "Leverage Your Strong Skills",
                "description": f"Highlight in interviews: {', '.join(names)}",
                "priority": "medium",
                "action": "Update your resume to emphasize these skills",
            })

        return recs

    # ── Utilities ──

    def _parse_json(self, value) -> list:
        if not value:
            return []
        if isinstance(value, list):
            return value
        if isinstance(value, str):
            try:
                parsed = json.loads(value)
                return parsed if isinstance(parsed, list) else []
            except (json.JSONDecodeError, TypeError):
                return []
        return []

    def save_to_db(self, user_id: int, result: Dict, resume_analysis_id: int = None, job_description_id: int = None) -> SkillGapAnalysis:
        """Persist the skill gap analysis to database and invalidate cache."""
        analysis = SkillGapAnalysis(
            user_id=user_id,
            resume_analysis_id=resume_analysis_id,
            job_description_id=job_description_id,
            matched_skills=json.dumps([s["skill"] for s in result["existing_skills"]]),
            missing_skills=json.dumps([s["skill"] for s in result["missing_skills"]]),
            additional_skills=json.dumps([s["skill"] for s in result["unused_skills"]]),
            priority_skills=json.dumps([s["skill"] for s in result["missing_skills"] if s["priority"] in ("critical", "high")]),
            match_percentage=result.get("match_percentage"),
        )
        self.db.add(analysis)
        self.db.commit()
        self.db.refresh(analysis)

        # Invalidate user's cache
        _analysis_cache.invalidate_user(user_id)

        return analysis

    def update_skill_analytics(self, user_id: int, result: Dict):
        """Update aggregated skill analytics for heatmap."""
        strong_skills = {s["skill"] for s in result.get("strong_skills", [])}
        weak_skills = {s["skill"] for s in result.get("weak_skills", [])}

        for skill_data in result.get("existing_skills", []):
            skill_name = skill_data["skill"]
            existing = self.db.query(SkillAnalytics).filter(
                SkillAnalytics.user_id == user_id,
                SkillAnalytics.skill_name == skill_name,
            ).first()

            category = self._get_skill_category(skill_name)
            if skill_name in strong_skills:
                proficiency = 80.0
            elif skill_name in weak_skills:
                proficiency = 40.0
            else:
                proficiency = 60.0

            if existing:
                existing.proficiency_level = max(existing.proficiency_level, proficiency)
                existing.category = category or existing.category
                existing.source = skill_data.get("source", existing.source)
                existing.last_assessed = datetime.now(timezone.utc)
                if skill_name in strong_skills:
                    existing.trend = "stable"
                elif skill_name in weak_skills:
                    existing.trend = "declining"
            else:
                self.db.add(SkillAnalytics(
                    user_id=user_id,
                    skill_name=skill_name,
                    category=category,
                    proficiency_level=proficiency,
                    source=skill_data.get("source", "resume"),
                    trend="stable",
                    last_assessed=datetime.now(timezone.utc),
                ))

        self.db.commit()

    def generate_career_recommendations(self, user_id: int, result: Dict):
        """Save recommendations to database (dedup by title+type)."""
        existing_recs = self.db.query(CareerRecommendation).filter(
            CareerRecommendation.user_id == user_id,
            CareerRecommendation.is_dismissed == False,
        ).all()
        existing_keys = {(r.recommendation_type, r.title) for r in existing_recs}

        for rec in result.get("recommendations", []):
            key = (rec.get("type", "career"), rec.get("title", ""))
            if key not in existing_keys:
                self.db.add(CareerRecommendation(
                    user_id=user_id,
                    recommendation_type=rec.get("type", "career"),
                    title=rec.get("title", ""),
                    description=rec.get("description", ""),
                    priority=rec.get("priority", "medium"),
                    reason=rec.get("action", ""),
                ))
                existing_keys.add(key)
        self.db.commit()

    def save_performance_metrics(self, user_id: int, metric_type: str, session_id: int, data: Dict):
        """Save performance metrics from interview or coding session."""
        metrics = PerformanceMetrics(
            user_id=user_id,
            metric_type=metric_type,
            session_id=session_id,
            overall_score=data.get("overall_score"),
            topic_scores=json.dumps(data.get("topic_scores", {})),
            weak_topics=json.dumps(data.get("weak_topics", [])),
            strong_topics=json.dumps(data.get("strong_topics", [])),
            difficulty_level=data.get("difficulty"),
            role=data.get("role"),
            completed_at=datetime.now(timezone.utc),
        )
        self.db.add(metrics)
        self.db.commit()
