"""Event-aware semantic retrieval over indexed F1 race-report chunks."""
from __future__ import annotations

import re

from rag.embeddings import embed_texts
from rag.vector_store import get_collection


def _normalize(text: str) -> str:
    """Normalize common Grand Prix / GP wording for simple event detection."""
    text = text.lower()
    text = re.sub(r"\bgp\b", "grand prix", text)
    text = re.sub(r"[^a-z0-9]+", " ", text)
    return re.sub(r"\s+", " ", text).strip()


def _build_metadata_filter(question: str, collection) -> dict | None:
    """Restrict retrieval to a named event and/or year when the query specifies one."""
    count = collection.count()
    if count == 0:
        return None

    normalized_question = _normalize(question)
    year_match = re.search(r"\b(19\d{2}|20\d{2})\b", question)
    requested_year = int(year_match.group(1)) if year_match else None

    result = collection.get(include=["metadatas"], limit=count)
    metadatas = result.get("metadatas") or []
    events: dict[str, str] = {}
    seasons: set[int] = set()

    for metadata in metadatas:
        if not metadata:
            continue
        event_name = metadata.get("event_name")
        if isinstance(event_name, str) and event_name.strip():
            events[event_name.strip()] = event_name.strip()
        season = metadata.get("season")
        if isinstance(season, int):
            seasons.add(season)

    # Match the longest event name first to reduce ambiguous short-name matches.
    matched_event = None
    for event_name in sorted(events.values(), key=len, reverse=True):
        normalized_event = _normalize(event_name)
        short_name = re.sub(r"\s+grand prix$", "", normalized_event).strip()
        if normalized_event in normalized_question or (
            len(short_name) >= 4 and re.search(rf"\b{re.escape(short_name)}\b", normalized_question)
        ):
            matched_event = event_name
            break

    conditions: list[dict] = []
    if matched_event:
        conditions.append({"event_name": {"$eq": matched_event}})
    if requested_year is not None:
        conditions.append({"season": {"$eq": requested_year}})

    if not conditions:
        return None
    if len(conditions) == 1:
        return conditions[0]
    return {"$and": conditions}


def retrieve_context(question: str, top_k: int = 5) -> list[dict]:
    """Retrieve semantically similar chunks, scoped to a named event/year where possible.

    If a user explicitly asks about a particular event, this intentionally does not fall
    back to unrelated races when that event has no indexed chunks.
    """
    if not question.strip():
        raise ValueError("question cannot be empty")

    collection = get_collection()
    count = collection.count()
    if count == 0:
        return []

    query_vector = embed_texts([question])[0]
    query_args = {
        "query_embeddings": [query_vector],
        "n_results": min(max(1, top_k), count),
        "include": ["documents", "metadatas", "distances"],
    }
    metadata_filter = _build_metadata_filter(question, collection)
    if metadata_filter is not None:
        query_args["where"] = metadata_filter

    result = collection.query(**query_args)
    documents = result.get("documents", [[]])[0] or []
    metadatas = result.get("metadatas", [[]])[0] or []
    distances = result.get("distances", [[]])[0] or []

    retrieved: list[dict] = []
    for document, metadata, distance in zip(documents, metadatas, distances):
        retrieved.append(
            {
                "text": document or "",
                "metadata": metadata or {},
                "distance": float(distance) if distance is not None else None,
            }
        )
    return retrieved
