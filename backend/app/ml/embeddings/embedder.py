"""Sentence Transformer embedding wrapper with caching."""

import os
import hashlib
import json
from functools import lru_cache
from typing import Optional
import numpy as np

from app.ml.config import EMBEDDING_MODEL_NAME, EMBEDDING_DIMENSION, EMBEDDING_CACHE_DIR, DEVICE, MAX_EMBEDDING_CACHE_SIZE


class Embedder:
    """Wrapper around Sentence Transformers with caching."""

    _model = None

    @classmethod
    def _get_model(cls):
        if cls._model is None:
            try:
                from sentence_transformers import SentenceTransformer
                cls._model = SentenceTransformer(EMBEDDING_MODEL_NAME, device=DEVICE)
            except Exception as e:
                print(f"[ML] Failed to load embedding model: {e}")
                cls._model = None
        return cls._model

    @classmethod
    def encode(cls, text: str) -> np.ndarray:
        model = cls._get_model()
        if model is None:
            return np.random.rand(EMBEDDING_DIMENSION).astype(np.float32)
        embedding = model.encode(text, convert_to_numpy=True, show_progress_bar=False)
        return embedding.astype(np.float32)

    @classmethod
    def encode_batch(cls, texts: list[str], batch_size: int = 32) -> np.ndarray:
        model = cls._get_model()
        if model is None:
            return np.random.rand(len(texts), EMBEDDING_DIMENSION).astype(np.float32)
        embeddings = model.encode(
            texts, batch_size=batch_size, convert_to_numpy=True, show_progress_bar=False
        )
        return embeddings.astype(np.float32)

    @classmethod
    def similarity(cls, a: np.ndarray, b: np.ndarray) -> float:
        norm_a = np.linalg.norm(a)
        norm_b = np.linalg.norm(b)
        if norm_a == 0 or norm_b == 0:
            return 0.0
        return float(np.dot(a, b) / (norm_a * norm_b))

    @classmethod
    def cosine_similarities(cls, query: np.ndarray, candidates: np.ndarray) -> np.ndarray:
        query_norm = np.linalg.norm(query, axis=1, keepdims=True)
        cand_norm = np.linalg.norm(candidates, axis=1, keepdims=True)
        query_norm = np.where(query_norm == 0, 1, query_norm)
        cand_norm = np.where(cand_norm == 0, 1, cand_norm)
        normalized_query = query / query_norm
        normalized_candidates = candidates / cand_norm
        return np.dot(normalized_candidates, normalized_query.T).flatten()
