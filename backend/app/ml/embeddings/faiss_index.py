"""FAISS index management for resume similarity search."""

import os
import json
import numpy as np
from typing import Optional
import joblib

from app.ml.config import FAISS_INDEX_PATH, FAISS_ID_MAP_PATH, EMBEDDING_DIMENSION


class FAISSIndex:
    """Manage FAISS index for resume embeddings."""

    def __init__(self):
        self.index = None
        self.id_map: dict[int, int] = {}
        self.reverse_id_map: dict[int, int] = {}
        self._next_id = 0

    def _get_index(self):
        if self.index is None:
            try:
                import faiss
                self.index = faiss.IndexFlatIP(EMBEDDING_DIMENSION)
                self._load()
            except ImportError:
                print("[ML] faiss not installed, using brute-force search")
                self.index = None
        return self.index

    def add(self, resume_id: int, embedding: np.ndarray) -> None:
        index = self._get_index()
        if index is None:
            return
        embedding = embedding.reshape(1, -1).astype(np.float32)
        import faiss
        faiss.normalize_L2(embedding)
        idx = self._next_id
        self.id_map[resume_id] = idx
        self.reverse_id_map[idx] = resume_id
        self._next_id += 1
        index.add(embedding)

    def search(self, query_embedding: np.ndarray, top_k: int = 10) -> list[tuple[int, float]]:
        index = self._get_index()
        if index is None or index.ntotal == 0:
            return []
        query = query_embedding.reshape(1, -1).astype(np.float32)
        import faiss
        faiss.normalize_L2(query)
        k = min(top_k, index.ntotal)
        distances, indices = index.search(query, k)
        results = []
        for dist, idx in zip(distances[0], indices[0]):
            if idx == -1:
                continue
            resume_id = self.reverse_id_map.get(int(idx))
            if resume_id is not None:
                results.append((resume_id, float(dist)))
        return results

    def remove(self, resume_id: int) -> bool:
        index = self._get_index()
        if index is None:
            return False
        if resume_id in self.id_map:
            del self.id_map[resume_id]
            return True
        return False

    def save(self) -> None:
        index = self._get_index()
        if index is None:
            return
        try:
            import faiss
            faiss.write_index(index, FAISS_INDEX_PATH)
            joblib.dump({
                "id_map": self.id_map,
                "reverse_id_map": self.reverse_id_map,
                "next_id": self._next_id,
            }, FAISS_ID_MAP_PATH)
        except Exception as e:
            print(f"[ML] Failed to save FAISS index: {e}")

    def _load(self) -> None:
        try:
            if os.path.exists(FAISS_INDEX_PATH) and os.path.exists(FAISS_ID_MAP_PATH):
                import faiss
                self.index = faiss.read_index(FAISS_INDEX_PATH)
                data = joblib.load(FAISS_ID_MAP_PATH)
                self.id_map = data["id_map"]
                self.reverse_id_map = data["reverse_id_map"]
                self._next_id = data["next_id"]
        except Exception as e:
            print(f"[ML] Failed to load FAISS index: {e}")

    @property
    def size(self) -> int:
        return self._next_id


_faiss_instance: Optional[FAISSIndex] = None


def get_faiss_index() -> FAISSIndex:
    global _faiss_instance
    if _faiss_instance is None:
        _faiss_instance = FAISSIndex()
    return _faiss_instance
