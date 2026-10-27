"""Persistent Chroma collection helpers."""
from __future__ import annotations

import chromadb

from rag.config import CHROMA_COLLECTION_NAME, CHROMA_PATH


def get_collection():
    """Return the persistent collection used by both indexing and querying."""
    CHROMA_PATH.mkdir(parents=True, exist_ok=True)
    client = chromadb.PersistentClient(path=str(CHROMA_PATH))
    return client.get_or_create_collection(
        name=CHROMA_COLLECTION_NAME,
        metadata={"hnsw:space": "cosine"},
    )
