"""Small deterministic router for the first hybrid-RAG version."""
from __future__ import annotations

import re

STAT_PATTERNS = [
    r"\bpoints?\b", r"\bwins?\b", r"\bwon\b", r"\bpodiums?\b",
    r"\bstandings\b", r"\bfastest lap\b", r"\bhow many\b",
    r"\bcount\b", r"\bnumber of (drivers|constructors|teams|races)\b",
    r"\bresults?\b", r"\bposition\b", r"\btop\s?\d+\b",
]
NARRATIVE_PATTERNS = [
    r"\bwhy\b", r"\bstrategy\b", r"\bexplain\b", r"\bexplanation\b",
    r"\bwhat happened\b", r"\bhow did\b", r"\breason\b", r"\banaly[sz]e\b",
    r"\bdescribe\b", r"\bcompare\b", r"\bwas it effective\b",
]


def classify_query(question: str) -> str:
    text = question.lower()
    has_stats = any(re.search(pattern, text) for pattern in STAT_PATTERNS)
    has_narrative = any(re.search(pattern, text) for pattern in NARRATIVE_PATTERNS)

    if has_stats and has_narrative:
        return "hybrid"
    if has_stats:
        return "stats"
    return "narrative"
