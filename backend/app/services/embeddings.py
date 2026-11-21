import os
from functools import lru_cache
import numpy as np
from sentence_transformers import SentenceTransformer

@lru_cache(maxsize=1)
def get_model():
    model_name = os.getenv("EMBEDDING_MODEL", "sentence-transformers/all-MiniLM-L6-v2")
    return SentenceTransformer(model_name)

def embed(text: str) -> list[float]:
    vector = get_model().encode([text], normalize_embeddings=True)[0]
    return vector.astype(float).tolist()

def cosine_from_normalized(a: list[float], b: list[float]) -> float:
    return float(np.dot(np.asarray(a, dtype=float), np.asarray(b, dtype=float)))
