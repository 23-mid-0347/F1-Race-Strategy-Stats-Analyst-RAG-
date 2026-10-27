"""Combine SQL analytics, event-aware retrieval, and local Ollama generation."""
from __future__ import annotations

import re

import httpx

from rag.config import DEFAULT_TOP_K, OLLAMA_BASE_URL, OLLAMA_CHAT_MODEL, OLLAMA_TIMEOUT_SECONDS
from rag.retriever import retrieve_context
from rag.router import classify_query
from rag.sql_analytics import answer_stats


def _plain_url(value: str | None) -> str:
    """Convert either a raw URL or Markdown-linked URL to a plain URL."""
    if not value:
        return ""
    value = value.strip()
    match = re.fullmatch(r"\[([^\]]+)\]\((https?://[^)]+)\)", value)
    return match.group(2) if match else value


def _generate_answer(question: str, route: str, sql_answer: str | None, passages: list[dict]) -> str:
    source_ids: dict[str, int] = {}
    context_blocks: list[str] = []

    for passage in passages:
        metadata = passage.get("metadata", {})
        source_url = _plain_url(metadata.get("source_url", ""))
        source_key = source_url or f"{metadata.get('title', 'F1 race report')}|{metadata.get('event_name', '')}"
        if source_key not in source_ids:
            source_ids[source_key] = len(source_ids) + 1
        source_number = source_ids[source_key]
        context_blocks.append(
            f"[Source {source_number}] {metadata.get('title', 'F1 race report')}\n"
            f"Event: {metadata.get('event_name', 'Unknown event')} ({metadata.get('season', 'Unknown season')})\n"
            f"URL: {source_url or 'not provided'}\n"
            f"Retrieval distance: {passage.get('distance')}\n"
            f"Excerpt: {passage.get('text', '')}"
        )

    context = "\n\n---\n\n".join(context_blocks) or "No relevant race-report excerpts were retrieved."

    system_prompt = (
        "You are an evidence-grounded Formula 1 analytics assistant. "
        "Use only the evidence actually supplied in this message. "
        "Treat assumptions in the question as unverified; correct false premises when evidence contradicts them. "
        "Never invent race facts, strategy decisions, lap times, standings, or causes. "
        "Answer the precise question in 2-4 sentences and do not add unrelated facts, season streaks, or standings. "
        "Do not contradict yourself. If an excerpt explicitly describes a tactical action, do not then claim that no strategy is mentioned. "
        "If the evidence does not explain a cause, state the specific evidence gap rather than guessing. "
        "If an event-specific SQL result identifies the winner of a named race, treat that as authoritative for that event; "
        "never use season-wide win totals as a substitute for an event result. "
        "Cite supported factual claims with exact numeric markers like [1] or [2] matching the provided source numbers. "
        "Never output [n], invent a source number, or cite a source that does not support the claim. "
        "When no SQL evidence is supplied, do not mention SQL or say a SQL result is missing."
    )
    prompt_parts = [f"Question: {question}", f"Query route: {route}"]
    if sql_answer:
        prompt_parts.append(f"Structured SQL evidence:\n{sql_answer}")
    prompt_parts.append(f"Retrieved race-report excerpts:\n{context}")
    prompt_parts.append(
        "Give a direct evidence-based answer. Correct any false premise. "
        "Cite claims only when the supplied SQL evidence or numbered report excerpt supports them. "
        "Do not use unsupported aggregate statistics to answer an event-specific question."
    )
    user_prompt = "\n\n".join(prompt_parts)

    try:
        response = httpx.post(
            f"{OLLAMA_BASE_URL}/api/chat",
            json={
                "model": OLLAMA_CHAT_MODEL,
                "stream": False,
                "messages": [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt},
                ],
                "options": {"temperature": 0.1},
            },
            timeout=OLLAMA_TIMEOUT_SECONDS,
        )
        response.raise_for_status()
        payload = response.json()
    except httpx.HTTPError as exc:
        raise RuntimeError(
            "Could not reach Ollama's chat API. Start Ollama and run "
            f"`ollama pull {OLLAMA_CHAT_MODEL}`. Details: {exc}"
        ) from exc

    answer = payload.get("message", {}).get("content", "").strip()
    # Prevent a literal citation placeholder from leaking into the UI if the model ignores instructions.
    answer = re.sub(r"\[n\]", "", answer, flags=re.IGNORECASE)
    answer = re.sub(r"[ \t]{2,}", " ", answer)
    if not answer:
        raise RuntimeError("Ollama returned an empty answer")
    return answer


def answer_question(question: str) -> dict:
    route = classify_query(question)
    sql_answer = answer_stats(question) if route in {"stats", "hybrid"} else None

    if route == "stats":
        if sql_answer is None:
            return {
                "answer": (
                    "I couldn't map that statistics question to a supported SQL template yet. "
                    "Currently supported: driver wins, podiums, driver/constructor standings, "
                    "race winners, fastest lap for a named event, and driver/constructor counts."
                ),
                "route": route,
                "sources": [],
            }
        return {"answer": sql_answer, "route": route, "sources": []}

    passages = retrieve_context(question, top_k=DEFAULT_TOP_K)
    if not passages:
        return {
            "answer": (
                "I couldn't find indexed passages for the specific race/year in your question. "
                "Check that its race report is indexed, or try a broader question."
            ),
            "route": route,
            "sources": [],
        }

    answer = _generate_answer(question, route, sql_answer, passages)
    sources: list[dict] = []
    seen_urls: set[str] = set()
    for passage in passages:
        metadata = passage.get("metadata", {})
        url = _plain_url(metadata.get("source_url", ""))
        if not url or url in seen_urls:
            continue
        seen_urls.add(url)
        sources.append({
            "title": metadata.get("title") or "F1 race report",
            "source_url": url,
            "event_name": metadata.get("event_name"),
            "season": metadata.get("season"),
            "distance": passage.get("distance"),
        })

    return {"answer": answer, "route": route, "sources": sources}
