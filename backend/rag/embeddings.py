"""Generate embeddings through the Ollama local HTTP API."""
from __future__ import annotations

import httpx

from rag.config import OLLAMA_BASE_URL, OLLAMA_EMBED_MODEL, OLLAMA_TIMEOUT_SECONDS


def embed_texts(texts: list[str], batch_size: int = 16) -> list[list[float]]:
    """Embed a list of strings; uses the same model for documents and queries."""
    clean_texts = [text.strip() for text in texts]
    if any(not text for text in clean_texts):
        raise ValueError("Cannot create embeddings for empty text")
    if not clean_texts:
        return []
    if batch_size < 1:
        raise ValueError("batch_size must be at least 1")

    all_vectors: list[list[float]] = []
    for start in range(0, len(clean_texts), batch_size):
        batch = clean_texts[start : start + batch_size]
        try:
            response = httpx.post(
                f"{OLLAMA_BASE_URL}/api/embed",
                json={"model": OLLAMA_EMBED_MODEL, "input": batch},
                timeout=OLLAMA_TIMEOUT_SECONDS,
            )
            response.raise_for_status()
            payload = response.json()
        except httpx.HTTPError as exc:
            raise RuntimeError(
                "Could not reach Ollama's embedding API. Start Ollama and run "
                f"`ollama pull {OLLAMA_EMBED_MODEL}`. Details: {exc}"
            ) from exc

        vectors = payload.get("embeddings")
        if not isinstance(vectors, list) or len(vectors) != len(batch):
            raise RuntimeError("Ollama returned an unexpected embeddings response")
        all_vectors.extend(vectors)

    return all_vectors
