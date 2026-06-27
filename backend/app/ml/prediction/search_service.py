"""Semantic resume search using FAISS embeddings."""

from app.ml.embeddings.embedder import Embedder
from app.ml.embeddings.faiss_index import get_faiss_index
from app.ml.utils.text_preprocessor import TextPreprocessor


class SearchService:
    """Semantic search for resumes using FAISS."""

    @staticmethod
    def index_resume(resume_id: int, resume_text: str) -> None:
        cleaned = TextPreprocessor.clean_text(resume_text)
        if not cleaned:
            return
        embedding = Embedder.encode(cleaned[:5000])
        faiss = get_faiss_index()
        faiss.add(resume_id, embedding)
        faiss.save()

    @staticmethod
    def search(query_text: str, top_k: int = 10) -> list[dict]:
        cleaned = TextPreprocessor.clean_text(query_text)
        if not cleaned:
            return []
        query_embedding = Embedder.encode(cleaned[:5000])
        faiss = get_faiss_index()
        results = faiss.search(query_embedding, top_k=top_k)
        return [
            {"resume_id": rid, "similarity": round(score, 4)}
            for rid, score in results
        ]

    @staticmethod
    def remove_resume(resume_id: int) -> bool:
        faiss = get_faiss_index()
        removed = faiss.remove(resume_id)
        if removed:
            faiss.save()
        return removed
