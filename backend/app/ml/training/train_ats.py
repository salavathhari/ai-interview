"""Train ATS score prediction model with synthetic data."""

import os
import random
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

import numpy as np
import joblib
from sklearn.model_selection import train_test_split

from app.ml.config import ATS_MODEL_PATH, MODELS_DIR
from app.ml.utils.metrics import regression_metrics


def generate_ats_data(n_samples: int = 1000) -> tuple[list[list[float]], list[float]]:
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

        score = 30.0
        if 200 <= word_count <= 800:
            score += 12
        elif word_count < 100:
            score -= 10
        elif word_count > 1500:
            score -= 3

        score += section_completeness * 18
        score += min(skill_count * 2.5, 15)
        score += min(experience_years * 1.5, 12)
        score += education_level * 3
        score += min(certification_count * 2, 10)
        score += keyword_density * 12
        if action_verb_density > 0.02:
            score += 5

        noise = random.gauss(0, 3)
        score = max(10, min(98, score + noise))

        X.append(features)
        y.append(round(score, 1))

    return X, y


def train():
    os.makedirs(MODELS_DIR, exist_ok=True)
    print("Generating synthetic ATS training data...")
    X, y = generate_ats_data(n_samples=1500)
    print(f"Generated {len(X)} samples")

    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

    print("Training XGBoost model...")
    try:
        from xgboost import XGBRegressor
        model = XGBRegressor(
            n_estimators=100, max_depth=6, learning_rate=0.1,
            random_state=42, objective="reg:squarederror"
        )
    except ImportError:
        print("XGBoost not available, using GradientBoostingRegressor")
        from sklearn.ensemble import GradientBoostingRegressor
        model = GradientBoostingRegressor(n_estimators=100, max_depth=6, learning_rate=0.1, random_state=42)

    X_train_np = np.array(X_train)
    X_test_np = np.array(X_test)
    y_train_np = np.array(y_train)
    y_test_np = np.array(y_test)

    model.fit(X_train_np, y_train_np)
    y_pred = model.predict(X_test_np)

    metrics = regression_metrics(y_test_np.tolist(), y_pred.tolist())
    print(f"\nRegression Metrics:")
    for k, v in metrics.items():
        if k != "confusion_matrix":
            print(f"  {k}: {v}")

    model_data = {"model": model, "feature_names": [
        "resume_length", "section_count", "skill_count", "experience_years",
        "project_count", "education_level", "certification_count",
        "keyword_density", "section_completeness", "action_verb_density",
    ]}
    joblib.dump(model_data, ATS_MODEL_PATH)
    print(f"\nModel saved to {ATS_MODEL_PATH}")
    return metrics


if __name__ == "__main__":
    train()
