"""Resume classification service."""

from app.ml.models.resume_classifier import ResumeClassifier


class ClassifierService:
    """High-level service for resume classification."""

    @staticmethod
    def classify(resume_text: str) -> dict:
        return ResumeClassifier.predict(resume_text)
