"""Multi-layer skill extraction using spaCy, dictionary, regex, and embeddings."""

import json
import re
import os
from typing import Optional
from app.ml.config import SKILL_DICT_PATH
from app.ml.embeddings.embedder import Embedder
from app.ml.config import SKILL_SIMILARITY_THRESHOLD
from app.ml.cache import ml_cache


class SkillExtractor:
    """Extract and categorize skills from resume text."""

    _skill_dict = None
    _all_skills = None
    _skill_embeddings = None
    _spacy_nlp = None

    @classmethod
    def _load_skill_dict(cls):
        if cls._skill_dict is None:
            try:
                with open(SKILL_DICT_PATH, "r") as f:
                    cls._skill_dict = json.load(f)
            except FileNotFoundError:
                cls._skill_dict = {"categories": {}}
        return cls._skill_dict

    @classmethod
    def _get_all_skills(cls):
        if cls._all_skills is None:
            data = cls._load_skill_dict()
            skills = []
            for cat_data in data.get("categories", {}).values():
                skills.extend(cat_data.get("skills", []))
            cls._all_skills = list(set(skills))
        return cls._all_skills

    @classmethod
    def _get_spacy(cls):
        if cls._spacy_nlp is None:
            try:
                import spacy
                try:
                    cls._spacy_nlp = spacy.load("en_core_web_sm")
                except OSError:
                    import subprocess
                    subprocess.run(["python", "-m", "spacy", "download", "en_core_web_sm"], capture_output=True)
                    cls._spacy_nlp = spacy.load("en_core_web_sm")
            except Exception:
                cls._spacy_nlp = None
        return cls._spacy_nlp

    @classmethod
    def _build_skill_embeddings(cls):
        if cls._skill_embeddings is None:
            all_skills = cls._get_all_skills()
            if not all_skills:
                cls._skill_embeddings = {"skills": [], "embeddings": []}
                return
            import numpy as np
            embeddings = Embedder.encode_batch(all_skills)
            cls._skill_embeddings = {
                "skills": all_skills,
                "embeddings": embeddings,
            }

    @classmethod
    def extract(cls, resume_text: str) -> dict:
        if not resume_text:
            return cls._empty_result()

        result, cached = ml_cache.cached("skills", resume_text, cls._extract_uncached)
        return result

    @classmethod
    def _extract_uncached(cls, resume_text: str) -> dict:
        dict_skills = cls._extract_by_dictionary(resume_text)
        regex_skills = cls._extract_by_regex(resume_text)
        spacy_skills = cls._extract_by_spacy(resume_text)

        all_detected = {}
        for skill in dict_skills:
            all_detected[skill] = True
        for skill in regex_skills:
            all_detected[skill] = True
        for skill in spacy_skills:
            all_detected[skill] = True

        categorized = cls._categorize(list(all_detected.keys()))
        categorized["all_skills"] = sorted(set(all_detected.keys()))
        return categorized

    @classmethod
    def extract_with_similarity(cls, resume_text: str, top_k: int = 20) -> dict:
        base_result = cls.extract(resume_text)
        cls._build_skill_embeddings()
        import numpy as np
        resume_embedding = Embedder.encode(resume_text)
        embeddings_data = cls._skill_embeddings
        if not embeddings_data["skills"]:
            return base_result

        emb_matrix = np.array(embeddings_data["embeddings"])
        query = resume_embedding.reshape(1, -1)
        sims = Embedder.cosine_similarities(query, emb_matrix)
        top_indices = np.argsort(sims)[::-1][:top_k]
        semantic_skills = []
        for idx in top_indices:
            if sims[idx] >= 0.3:
                semantic_skills.append({
                    "skill": embeddings_data["skills"][idx],
                    "similarity": round(float(sims[idx]), 3),
                })

        base_result["semantic_matches"] = semantic_skills
        return base_result

    @classmethod
    def _extract_by_dictionary(cls, text: str) -> list[str]:
        data = cls._load_skill_dict()
        text_lower = text.lower()
        detected = []
        for cat_data in data.get("categories", {}).values():
            for skill in cat_data.get("skills", []):
                pattern = r"\b" + re.escape(skill.lower()) + r"\b"
                if re.search(pattern, text_lower):
                    detected.append(skill)
            for alias, canonical in cat_data.get("aliases", {}).items():
                pattern = r"\b" + re.escape(alias.lower()) + r"\b"
                if re.search(pattern, text_lower):
                    detected.append(canonical)
        return list(set(detected))

    @classmethod
    def _extract_by_regex(cls, text: str) -> list[str]:
        patterns = [
            (r"\b(?:React\.js|ReactJS|React JS)\b", "React"),
            (r"\b(?:Node\.js|NodeJS|Node JS)\b", "Node.js"),
            (r"\b(?:Vue\.js|VueJS|Vue JS)\b", "Vue.js"),
            (r"\b(?:Next\.js|NextJS|Next JS)\b", "Next.js"),
            (r"\b(?:Nuxt\.js|NuxtJS|Nuxt JS)\b", "Nuxt.js"),
            (r"\b(?:Tailwind\.css|TailwindCSS|Tailwind CSS)\b", "Tailwind CSS"),
            (r"\b(?:Express\.js|ExpressJS|Express JS)\b", "Express"),
            (r"\b(?:TypeScript|Type Script|TS)\b", "TypeScript"),
            (r"\b(?:JavaScript|JavaScript|JS)\b", "JavaScript"),
            (r"\b(?:C Sharp|C#)\b", "C#"),
            (r"\b(?:Go Lang|Golang|Go)\b", "Go"),
            (r"\b(?:Rust Lang|RS)\b", "Rust"),
            (r"\b(?:K8s|Kubernetes)\b", "Kubernetes"),
            (r"\b(?:CI/CD|CICD|Continuous Integration|Continuous Deployment)\b", "CI/CD"),
            (r"\b(?:AWS|Amazon Web Services)\b", "AWS"),
            (r"\b(?:GCP|Google Cloud Platform|Google Cloud)\b", "GCP"),
            (r"\b(?:Azure|Microsoft Azure)\b", "Azure"),
            (r"\b(?:ML|Machine Learning)\b", "Machine Learning"),
            (r"\b(?:DL|Deep Learning)\b", "Deep Learning"),
            (r"\b(?:NLP|Natural Language Processing)\b", "NLP"),
            (r"\b(?:TF|TensorFlow)\b", "TensorFlow"),
            (r"\b(?:PyTorch|Py Torch)\b", "PyTorch"),
            (r"\b(?:sklearn|scikit learn|Scikit-learn)\b", "scikit-learn"),
            (r"\b(?:REST\s*(?:API|api))\b", "REST API"),
            (r"\b(?:GraphQL|Graph QL)\b", "GraphQL"),
            (r"\b(?:gRPC|GRPC)\b", "gRPC"),
            (r"\b(?:Postgres|PostgreSQL)\b", "PostgreSQL"),
            (r"\b(?:Mongo|MongoDB)\b", "MongoDB"),
            (r"\b(?:Terraform|tf)\b", "Terraform"),
            (r"\b(?:Ansible)\b", "Ansible"),
            (r"\b(?:Jenkins)\b", "Jenkins"),
            (r"\b(?:Docker)\b", "Docker"),
        ]
        detected = []
        for pattern, skill in patterns:
            if re.search(pattern, text, re.IGNORECASE):
                detected.append(skill)
        return detected

    @classmethod
    def _extract_by_spacy(cls, text: str) -> list[str]:
        nlp = cls._get_spacy()
        if nlp is None:
            return []
        doc = nlp(text[:10000])
        skills = []
        tech_terms = {
            "python", "java", "javascript", "typescript", "react", "angular", "vue",
            "docker", "kubernetes", "aws", "azure", "gcp", "terraform", "ansible",
            "jenkins", "github", "gitlab", "linux", "redis", "graphql", "postgresql",
            "mongodb", "mysql", "flask", "django", "fastapi", "spring", "node",
            "tensorflow", "pytorch", "pandas", "numpy", "scikit", "spark",
        }
        for token in doc:
            if token.text.lower() in tech_terms:
                skills.append(token.text)
        for ent in doc.ents:
            if ent.label_ in ("ORG", "PRODUCT"):
                entity_text = ent.text.strip()
                if "," in entity_text:
                    for part in entity_text.split(","):
                        part = part.strip()
                        if any(t in part.lower() for t in tech_terms):
                            skills.append(part)
                else:
                    if any(t in entity_text.lower() for t in tech_terms):
                        skills.append(entity_text)

        normalized = []
        normalization_map = {
            "react.js": "React", "reactjs": "React", "react js": "React",
            "node.js": "Node.js", "nodejs": "Node.js", "node js": "Node.js",
            "vue.js": "Vue.js", "vuejs": "Vue.js",
            "next.js": "Next.js", "nextjs": "Next.js",
            "angular.js": "Angular", "angularjs": "Angular",
            "typescript": "TypeScript", "type script": "TypeScript",
            "javascript": "JavaScript", "java script": "JavaScript",
            "postgresql": "PostgreSQL", "postgres": "PostgreSQL",
            "mongodb": "MongoDB", "mongo": "MongoDB",
            "kubernetes": "Kubernetes", "k8s": "Kubernetes",
            "amazon web services": "AWS",
            "google cloud platform": "GCP", "google cloud": "GCP",
            "microsoft azure": "Azure",
            "machine learning": "Machine Learning",
            "deep learning": "Deep Learning",
            "natural language processing": "NLP",
            "scikit-learn": "scikit-learn", "sklearn": "scikit-learn",
        }
        for skill in skills:
            key = skill.lower().strip()
            normalized_name = normalization_map.get(key, skill)
            if normalized_name not in normalized:
                normalized.append(normalized_name)

        return normalized

    @classmethod
    def _categorize(cls, skills: list[str]) -> dict:
        data = cls._load_skill_dict()
        result = {}
        for cat_name, cat_data in data.get("categories", {}).items():
            cat_skills = cat_data.get("skills", [])
            found = [s for s in skills if s in cat_skills or s.lower() in [c.lower() for c in cat_skills]]
            if found:
                result[cat_name] = found
        return result

    @staticmethod
    def _empty_result() -> dict:
        return {
            "programming_languages": [],
            "frameworks": [],
            "databases": [],
            "cloud_platforms": [],
            "devops_tools": [],
            "ai_frameworks": [],
            "soft_skills": [],
            "operating_systems": [],
            "methodologies": [],
            "all_skills": [],
        }
