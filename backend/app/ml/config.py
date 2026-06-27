"""ML Configuration — device detection, paths, constants."""

import os
try:
    import torch
    _HAS_TORCH = True
except ImportError:
    _HAS_TORCH = False

ML_ROOT = os.path.dirname(os.path.abspath(__file__))

# Paths
MODELS_DIR = os.path.join(ML_ROOT, "models", "saved")
DATASETS_DIR = os.path.join(ML_ROOT, "datasets")
EMBEDDING_CACHE_DIR = os.path.join(ML_ROOT, "embeddings", "cache")
FAISS_INDEX_DIR = os.path.join(ML_ROOT, "embeddings", "indices")

# Ensure directories exist
for d in [MODELS_DIR, DATASETS_DIR, EMBEDDING_CACHE_DIR, FAISS_INDEX_DIR]:
    os.makedirs(d, exist_ok=True)

# Device
DEVICE = "cuda" if _HAS_TORCH and torch.cuda.is_available() else "cpu"

# Embedding model
EMBEDDING_MODEL_NAME = "all-MiniLM-L6-v2"
EMBEDDING_DIMENSION = 384

# Classification
CLASSIFICATION_MODEL_PATH = os.path.join(MODELS_DIR, "resume_classifier.joblib")
ATS_MODEL_PATH = os.path.join(MODELS_DIR, "ats_predictor.joblib")
QUALITY_MODEL_PATH = os.path.join(MODELS_DIR, "quality_predictor.joblib")
RECOMMENDER_MODEL_PATH = os.path.join(MODELS_DIR, "job_recommender_model.joblib")

# FAISS
FAISS_INDEX_PATH = os.path.join(FAISS_INDEX_DIR, "resume_index.faiss")
FAISS_ID_MAP_PATH = os.path.join(FAISS_INDEX_DIR, "resume_id_map.joblib")

# Skill dictionary
SKILL_DICT_PATH = os.path.join(DATASETS_DIR, "skill_dictionary.json")
JOB_ROLES_PATH = os.path.join(DATASETS_DIR, "job_roles.json")
CAREER_PATHS_PATH = os.path.join(DATASETS_DIR, "career_paths.json")
ATS_KNOWLEDGE_PATH = os.path.join(DATASETS_DIR, "ats_knowledge.json")

# Performance
MAX_EMBEDDING_CACHE_SIZE = 1000
PREDICTION_TIMEOUT_MS = 300
BATCH_SIZE = 32

# Confidence thresholds
CLASSIFICATION_CONFIDENCE_THRESHOLD = 0.5
SKILL_SIMILARITY_THRESHOLD = 0.75
SKILL_PARTIAL_THRESHOLD = 0.50
