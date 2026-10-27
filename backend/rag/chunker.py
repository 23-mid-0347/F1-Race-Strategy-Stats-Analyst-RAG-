"""Simple word-based chunking for race reports."""
from __future__ import annotations


def chunk_text(text: str, chunk_words: int = 350, overlap_words: int = 60) -> list[str]:
    """Split text into overlapping chunks measured in words.

    350 words is roughly 400–500 tokens for typical English prose. Word-based
    chunking avoids adding a tokenizer dependency to the first implementation.
    """
    if chunk_words < 1:
        raise ValueError("chunk_words must be at least 1")
    if overlap_words < 0 or overlap_words >= chunk_words:
        raise ValueError("overlap_words must be >= 0 and less than chunk_words")

    words = text.split()
    if not words:
        return []

    step = chunk_words - overlap_words
    chunks: list[str] = []
    start = 0
    while start < len(words):
        part = words[start : start + chunk_words]
        if not part:
            break
        chunks.append(" ".join(part))
        if start + chunk_words >= len(words):
            break
        start += step
    return chunks
