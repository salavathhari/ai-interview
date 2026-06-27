"""Train resume quality prediction model with synthetic data."""

import os
import random
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

import numpy as np
import joblib
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier

from app.ml.config import QUALITY_MODEL_PATH, MODELS_DIR


def generate_quality_data(n_samples: int = 1000) -> tuple[list[list[float]], list[str]]:
    X = []
    y = []
    for _ in range(n_samples):
        word_count = random.randint(50, 2000)
        section_count = random.randint(1, 8)
        skill_count = random.randint(0, 25)
        experience_years = random.randint(0, 20)
        project_count = random.randint(0, 10)
        education_level = random.choice([0, 1, 2, 3, 4, 5])
        certification_count = random.randint(0, 8)
        keyword_density = round(random.uniform(0, 1.0), 2)
        section_completeness = round(random.uniform(0, 1.0), 2)
        action_verb_density = round(random.uniform(0, 0.08), 3)

        features = [
            word_count, section_count, skill_count, experience_years,
            project_count, education_level, certification_count,
            keyword_density, section_completeness, action_verb_density,
        ]

        # Randomly pick a target quality to ensure balance
        target = random.choice(["Poor", "Average", "Good", "Excellent"])

        if target == "Poor":
            # Generate features that produce a low score
            word_count = random.randint(30, 120)
            section_count = random.randint(1, 2)
            skill_count = random.randint(0, 3)
            experience_years = random.randint(0, 1)
            project_count = 0
            education_level = random.choice([0, 1])
            certification_count = 0
            keyword_density = round(random.uniform(0, 0.15), 2)
            section_completeness = round(random.uniform(0, 0.25), 2)
            action_verb_density = round(random.uniform(0, 0.01), 3)
        elif target == "Average":
            word_count = random.randint(100, 350)
            section_count = random.randint(2, 4)
            skill_count = random.randint(2, 8)
            experience_years = random.randint(0, 3)
            project_count = random.randint(0, 2)
            education_level = random.choice([1, 2, 3])
            certification_count = random.randint(0, 2)
            keyword_density = round(random.uniform(0.1, 0.4), 2)
            section_completeness = round(random.uniform(0.25, 0.5), 2)
            action_verb_density = round(random.uniform(0.005, 0.025), 3)
        elif target == "Good":
            word_count = random.randint(250, 800)
            section_count = random.randint(3, 6)
            skill_count = random.randint(5, 15)
            experience_years = random.randint(1, 8)
            project_count = random.randint(1, 5)
            education_level = random.choice([2, 3, 4])
            certification_count = random.randint(0, 4)
            keyword_density = round(random.uniform(0.25, 0.65), 2)
            section_completeness = round(random.uniform(0.5, 0.8), 2)
            action_verb_density = round(random.uniform(0.015, 0.045), 3)
        else:  # Excellent
            word_count = random.randint(400, 1200)
            section_count = random.randint(5, 8)
            skill_count = random.randint(10, 25)
            experience_years = random.randint(3, 15)
            project_count = random.randint(3, 10)
            education_level = random.choice([3, 4, 5])
            certification_count = random.randint(2, 8)
            keyword_density = round(random.uniform(0.4, 0.9), 2)
            section_completeness = round(random.uniform(0.75, 1.0), 2)
            action_verb_density = round(random.uniform(0.025, 0.07), 3)

        features = [
            word_count, section_count, skill_count, experience_years,
            project_count, education_level, certification_count,
            keyword_density, section_completeness, action_verb_density,
        ]

        score = 30
        if 200 <= word_count <= 800:
            score += 12
        elif word_count < 100:
            score -= 10

        score += section_completeness * 20
        score += min(skill_count, 10)
        score += min(experience_years * 2, 10)
        score += education_level * 2
        score += min(certification_count * 2, 6)
        score += keyword_density * 10
        if action_verb_density > 0.02:
            score += 5

        noise = random.gauss(0, 3)
        final_score = max(0, min(100, score + noise))

        if final_score < 35:
            quality = "Poor"
        elif final_score < 55:
            quality = "Average"
        elif final_score < 75:
            quality = "Good"
        else:
            quality = "Excellent"

        X.append(features)
        y.append(quality)

    return X, y


def train():
    os.makedirs(MODELS_DIR, exist_ok=True)
    print("Generating synthetic quality training data...")
    X, y = generate_quality_data(n_samples=1500)
    print(f"Generated {len(X)} samples, distribution: {dict((l, y.count(l)) for l in set(y))}")

    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42, stratify=y)

    print("Training Random Forest model...")
    model = RandomForestClassifier(n_estimators=100, max_depth=10, random_state=42)
    model.fit(np.array(X_train), np.array(y_train))
    y_pred = model.predict(np.array(X_test))

    accuracy = sum(1 for true, pred in zip(y_test, y_pred) if true == pred) / len(y_test)
    print(f"Accuracy: {accuracy * 100:.1f}%")

    from sklearn.metrics import classification_report
    print("\nClassification Report:")
    print(classification_report(y_test, y_pred))

    model_data = {"model": model, "feature_names": [
        "resume_length", "section_count", "skill_count", "experience_years",
        "project_count", "education_level", "certification_count",
        "keyword_density", "section_completeness", "action_verb_density",
    ]}
    joblib.dump(model_data, QUALITY_MODEL_PATH)
    print(f"\nModel saved to {QUALITY_MODEL_PATH}")
    return accuracy


if __name__ == "__main__":
    train()
