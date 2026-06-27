"""Train resume classification model with synthetic data."""

import os
import random
import re
import sys
import joblib
import numpy as np

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.svm import LinearSVC
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import train_test_split
from sklearn.metrics import classification_report, accuracy_score

from app.ml.config import CLASSIFICATION_MODEL_PATH, MODELS_DIR


RESUME_TEMPLATES = {
    "Frontend Developer": [
        "Experienced {lang} developer with expertise in {framework}. Built responsive web applications using {tech}. Proficient in HTML, CSS, JavaScript. Experience with {tool}.",
        "Frontend engineer skilled in {framework} and {lang}. Developed single-page applications with {tech}. Knowledge of responsive design and accessibility.",
        "Web developer specializing in {framework}. Proficient in {lang}, HTML5, CSS3, {tech}. Built component-based UIs with state management.",
    ],
    "Backend Developer": [
        "Backend developer with {years} years experience in {lang}. Built RESTful APIs using {framework}. Expertise in {db} and {tool}.",
        "Server-side engineer proficient in {lang} and {framework}. Designed database schemas in {db}. Experience with {tool} and microservices.",
        "Software engineer specializing in backend development. Built scalable APIs with {framework} in {lang}. Expertise in {db} and cloud deployment.",
    ],
    "Full Stack Developer": [
        "Full stack developer proficient in {lang} and {framework}. Built end-to-end web applications with {db} and {tool}. Experience with {cloud}.",
        "Versatile developer skilled in both frontend ({tech}) and backend ({framework}). Built complete web solutions with {db} and {cloud}.",
        "Full stack engineer with expertise in {lang}, {framework}, and {db}. Deployed applications on {cloud} using {tool}.",
    ],
    "Cloud Native Engineer": [
        "Cloud engineer with expertise in {cloud}. Designed cloud architectures using {tool}. Experience with containerization and orchestration.",
        "Infrastructure engineer skilled in {cloud} and {tool}. Built scalable cloud-native applications with {tech}. Knowledge of DevOps practices.",
        "Cloud solutions architect with {cloud} certification. Implemented infrastructure as code using {tool}. Experience with container orchestration.",
    ],
    "DevOps Engineer": [
        "DevOps engineer with expertise in {tool} and {cloud}. Implemented CI/CD pipelines and automated deployments. Skilled in monitoring and logging.",
        "Site reliability engineer proficient in {tool} and {cloud}. Built automated infrastructure with {tech}. Experience with container orchestration.",
        "Infrastructure automation engineer skilled in {tool} and {cloud}. Implemented monitoring, alerting, and incident response systems.",
    ],
    "AI Engineer": [
        "AI engineer with expertise in {lang} and {ml_tool}. Built machine learning models using {ml_framework}. Experience with deep learning and NLP.",
        "Machine learning engineer proficient in {ml_framework} and {lang}. Developed and deployed AI models. Expertise in {ml_tool} and data processing.",
        "AI/ML engineer with {years} years experience. Built computer vision and NLP systems using {ml_framework}. Skilled in {lang} and {ml_tool}.",
    ],
    "Data Scientist": [
        "Data scientist proficient in {lang}, {ml_tool}, and SQL. Performed statistical analysis and built predictive models. Experience with data visualization.",
        "Analytics professional skilled in {lang} and {ml_tool}. Built machine learning models and performed A/B testing. Expertise in data storytelling.",
        "Data scientist with expertise in {lang}, {ml_tool}, and {db}. Built recommendation systems and predictive models. Skilled in data wrangling.",
    ],
    "Mobile Developer": [
        "Mobile developer proficient in {mobile_framework} and {lang}. Built cross-platform mobile applications. Experience with {db} and API integration.",
        "iOS/Android developer skilled in {mobile_framework}. Built responsive mobile UIs with {lang}. Experience with app deployment and testing.",
        "Mobile application developer with expertise in {mobile_framework} and {lang}. Built real-time mobile apps with backend integration.",
    ],
    "UI/UX Designer": [
        "UI/UX designer with expertise in Figma and {tool}. Created user-centered designs and prototypes. Experience with design systems and usability testing.",
        "Product designer skilled in wireframing, prototyping, and user research. Proficient in {tool} and design thinking methodology.",
        "UX designer with experience in user research, interaction design, and visual design. Created design systems using {tool}.",
    ],
    "Cybersecurity Engineer": [
        "Security engineer with expertise in {tool} and {lang}. Performed penetration testing and vulnerability assessments. Knowledge of OWASP and security frameworks.",
        "Cybersecurity professional skilled in network security and incident response. Proficient in {tool} and security auditing. Experience with compliance frameworks.",
        "Information security engineer with expertise in {tool}. Conducted security assessments and implemented security controls. Knowledge of cryptography.",
    ],
}

SKILL_POOLS = {
    "lang": ["Python", "JavaScript", "TypeScript", "Java", "C++", "Go", "Rust", "Ruby", "Kotlin", "Swift"],
    "framework": ["Django", "FastAPI", "Flask", "Spring Boot", "Express", "Node.js", "ASP.NET"],
    "tech": ["React", "Angular", "Vue.js", "Next.js", "Node.js", "GraphQL", "REST API", "gRPC"],
    "tool": ["Docker", "Kubernetes", "Jenkins", "Git", "GitHub Actions", "Terraform", "Ansible", "Figma"],
    "db": ["PostgreSQL", "MySQL", "MongoDB", "Redis", "Elasticsearch", "DynamoDB"],
    "cloud": ["AWS", "Azure", "GCP", "DigitalOcean", "Heroku"],
    "ml_tool": ["Pandas", "NumPy", "scikit-learn", "Jupyter", "SQL", "Tableau"],
    "ml_framework": ["TensorFlow", "PyTorch", "Keras", "scikit-learn", "Hugging Face Transformers"],
    "mobile_framework": ["React Native", "Flutter", "SwiftUI", "Jetpack Compose"],
}


def generate_synthetic_data(samples_per_class: int = 200) -> tuple[list[str], list[str]]:
    texts = []
    labels = []
    for role, templates in RESUME_TEMPLATES.items():
        for _ in range(samples_per_class):
            template = random.choice(templates)
            filled = template
            for pool_key, pool_values in SKILL_POOLS.items():
                if "{" + pool_key + "}" in filled:
                    selected = random.sample(pool_values, min(3, len(pool_values)))
                    filled = filled.replace("{" + pool_key + "}", ", ".join(selected))
            filled = filled.replace("{years}", str(random.randint(1, 10)))
            filled = re.sub(r"\{[^}]+\}", "general software development", filled)
            texts.append(filled)
            labels.append(role)
    return texts, labels


def train():
    os.makedirs(MODELS_DIR, exist_ok=True)
    print("Generating synthetic training data...")
    texts, labels = generate_synthetic_data(samples_per_class=250)
    print(f"Generated {len(texts)} samples across {len(set(labels))} classes")

    X_train, X_test, y_train, y_test = train_test_split(
        texts, labels, test_size=0.2, random_state=42, stratify=labels
    )

    print("Training TF-IDF + LinearSVC...")
    vectorizer = TfidfVectorizer(max_features=10000, ngram_range=(1, 2), stop_words="english")
    X_train_vec = vectorizer.fit_transform(X_train)
    X_test_vec = vectorizer.transform(X_test)

    model = LinearSVC(C=1.0, max_iter=10000)
    model.fit(X_train_vec, y_train)
    y_pred = model.predict(X_test_vec)

    accuracy = accuracy_score(y_test, y_pred)
    print(f"Accuracy: {accuracy * 100:.1f}%")
    print("\nClassification Report:")
    print(classification_report(y_test, y_pred))

    model_data = {"model": model, "vectorizer": vectorizer}
    joblib.dump(model_data, CLASSIFICATION_MODEL_PATH)
    print(f"\nModel saved to {CLASSIFICATION_MODEL_PATH}")
    return accuracy


if __name__ == "__main__":
    train()
