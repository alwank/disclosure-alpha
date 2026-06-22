import logging
import os
from functools import lru_cache

import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

_logger = logging.getLogger(__name__)
_tfidf_fallback_warned = False


def _warn_tfidf_fallback() -> None:
    global _tfidf_fallback_warned
    if not _tfidf_fallback_warned:
        _tfidf_fallback_warned = True
        _logger.warning(
            "sentence-transformers unavailable; using TF-IDF embeddings "
            "(install disclosure-alpha[semantic] or set EMBEDDING_BACKEND=tfidf)"
        )


@lru_cache(maxsize=1)
def _get_sentence_model():
    # ponytail: lazy-load heavy model; tests can set EMBEDDING_BACKEND=tfidf
    if os.getenv("EMBEDDING_BACKEND", "").lower() == "tfidf":
        return None
    try:
        from sentence_transformers import SentenceTransformer

        return SentenceTransformer("all-MiniLM-L6-v2")
    except Exception:
        _warn_tfidf_fallback()
        return None


def _chunk_text(text: str, max_chars: int = 2000) -> list[str]:
    paragraphs = [p.strip() for p in text.split("\n") if p.strip()]
    if not paragraphs:
        return [""]
    chunks: list[str] = []
    current = ""
    for p in paragraphs:
        if len(current) + len(p) + 1 <= max_chars:
            current = f"{current}\n{p}".strip()
        else:
            if current:
                chunks.append(current)
            current = p
    if current:
        chunks.append(current)
    return chunks or [text[:max_chars]]


def _tfidf_embedding(text: str) -> np.ndarray:
    vec = TfidfVectorizer(max_features=512)
    matrix = vec.fit_transform([text or " "])
    return matrix.toarray()[0]


def embed_text(text: str) -> np.ndarray:
    model = _get_sentence_model()
    if model is None:
        return _tfidf_embedding(text)
    chunks = _chunk_text(text)
    embeddings = model.encode(chunks, show_progress_bar=False)
    return np.mean(embeddings, axis=0)


def semantic_similarity(text_a: str, text_b: str) -> float:
    if not text_a.strip() or not text_b.strip():
        return 0.0
    model = _get_sentence_model()
    if model is None:
        vec = TfidfVectorizer(max_features=512)
        matrix = vec.fit_transform([text_a, text_b])
        sim = cosine_similarity(matrix[0:1], matrix[1:2])[0][0]
        return float(max(0.0, min(1.0, sim)))
    emb_a = embed_text(text_a)
    emb_b = embed_text(text_b)
    denom = np.linalg.norm(emb_a) * np.linalg.norm(emb_b)
    if denom == 0:
        return 0.0
    sim = float(np.dot(emb_a, emb_b) / denom)
    return max(0.0, min(1.0, sim))
