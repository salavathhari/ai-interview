"""Tests for the ML module."""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from app.ml.utils.text_preprocessor import TextPreprocessor
from app.ml.utils.feature_engineer import FeatureEngineer
from app.ml.models.resume_classifier import ResumeClassifier
from app.ml.models.ats_predictor import ATSPredictor
from app.ml.models.quality_predictor import QualityPredictor
from app.ml.models.skill_extractor import SkillExtractor


class TestTextPreprocessor:
    def test_clean_text(self):
        text = "Hello   World\t\t\n\nTest"
        result = TextPreprocessor.clean_text(text)
        assert "Hello World Test" == result

    def test_word_count(self):
        assert TextPreprocessor.word_count("Hello World") == 2
        assert TextPreprocessor.word_count("") == 0

    def test_section_completeness(self):
        text = "Experience: Worked at Google\nEducation: BS in CS\nSkills: Python, Java\nProjects: Built an app"
        score = TextPreprocessor.section_completeness(text)
        assert score == 1.0

    def test_empty_text(self):
        assert TextPreprocessor.clean_text("") == ""
        assert TextPreprocessor.word_count("") == 0


class TestFeatureEngineer:
    def test_extract_features(self):
        text = """Experience: Software Engineer at Google (2020-2024)
Education: Bachelor of Science in Computer Science
Skills: Python, JavaScript, React, Docker, AWS
Projects: Built a scalable web application
Certifications: AWS Certified Developer"""
        features = FeatureEngineer.extract_all_features(text)
        assert features["resume_length"] > 0
        assert features["section_count"] > 0
        assert features["education_level"] >= 3

    def test_feature_vector(self):
        features = {
            "resume_length": 500,
            "section_count": 5,
            "skill_count": 8,
            "experience_years": 3,
            "project_count": 2,
            "education_level": 3,
            "certification_count": 1,
            "keyword_density": 0.4,
            "section_completeness": 0.75,
            "action_verb_density": 0.03,
        }
        vector = FeatureEngineer.get_feature_vector(features)
        assert len(vector) == 10
        assert vector[0] == 500.0


class TestResumeClassifier:
    def test_heuristic_predict_frontend(self):
        text = "Frontend developer with React, Angular, Vue.js, HTML, CSS, JavaScript expertise"
        result = ResumeClassifier.predict(text)
        assert "predicted_role" in result
        assert "confidence" in result
        assert result["predicted_role"] == "Frontend Developer"

    def test_heuristic_predict_backend(self):
        text = "Backend developer with Python, Django, FastAPI, PostgreSQL, REST API, Docker"
        result = ResumeClassifier.predict(text)
        assert result["predicted_role"] == "Backend Developer"

    def test_heuristic_predict_devops(self):
        text = "DevOps engineer with Docker, Kubernetes, Jenkins, CI/CD, Terraform, AWS, monitoring"
        result = ResumeClassifier.predict(text)
        assert result["predicted_role"] == "DevOps Engineer"

    def test_heuristic_predict_ai(self):
        text = "AI engineer with machine learning, deep learning, TensorFlow, PyTorch, NLP, neural networks"
        result = ResumeClassifier.predict(text)
        assert result["predicted_role"] == "AI Engineer"


class TestATSPredictor:
    def test_heuristic_predict(self):
        features = {
            "resume_length": 500,
            "section_count": 5,
            "skill_count": 8,
            "experience_years": 3,
            "project_count": 2,
            "education_level": 3,
            "certification_count": 1,
            "keyword_density": 0.5,
            "section_completeness": 0.75,
            "action_verb_density": 0.03,
        }
        result = ATSPredictor.predict(features)
        assert "ats_score" in result
        assert "confidence" in result
        assert 0 <= result["ats_score"] <= 100

    def test_empty_features(self):
        result = ATSPredictor.predict({})
        assert "ats_score" in result


class TestQualityPredictor:
    def test_heuristic_predict(self):
        features = {
            "resume_length": 500,
            "section_count": 5,
            "skill_count": 8,
            "experience_years": 3,
            "project_count": 2,
            "education_level": 3,
            "certification_count": 1,
            "keyword_density": 0.5,
            "section_completeness": 0.75,
            "action_verb_density": 0.03,
        }
        result = QualityPredictor.predict(features)
        assert "quality" in result
        assert result["quality"] in ["Poor", "Average", "Good", "Excellent"]


class TestSkillExtractor:
    def test_extract_skills(self):
        text = "Experienced developer with Python, JavaScript, React, Docker, AWS, PostgreSQL"
        result = SkillExtractor.extract(text)
        assert "all_skills" in result
        assert len(result["all_skills"]) > 0
        assert "Python" in result["all_skills"]

    def test_categorization(self):
        text = "Full stack developer with React, Node.js, PostgreSQL, Docker, AWS"
        result = SkillExtractor.extract(text)
        assert "frameworks" in result or "databases" in result or "cloud_platforms" in result


if __name__ == "__main__":
    import pytest
    pytest.main([__file__, "-v"])
