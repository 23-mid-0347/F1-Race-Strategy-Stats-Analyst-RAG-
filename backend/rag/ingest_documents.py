"""Fetch 2023 F1 race articles from Wikipedia and index them into Chroma."""
from __future__ import annotations

import re
import sys
import time
from datetime import datetime
from urllib.parse import quote

import httpx
from sqlalchemy import delete, select
from sqlalchemy.orm import Session

# Import configuration before the DB connection so root/backend .env files load.
from rag.config import DEFAULT_SEASON
from rag.chunker import chunk_text
from rag.embeddings import embed_texts
from rag.vector_store import get_collection
from database.connection import get_engine
from database.models import Document, EmbeddingMetadata, Event, Season

WIKIPEDIA_API = "https://en.wikipedia.org/w/api.php"
USER_AGENT = (
    "F1HybridRAGBot/0.2 "
    "(https://github.com/23-mid-0347/F1-Race-Strategy-Stats-Analyst-RAG-) "
    f"httpx/{httpx.__version__}"
)


def fetch_wikipedia_article(client: httpx.Client, requested_title: str) -> tuple[str, str, str] | None:
    """Return (canonical title, plain-text extract, canonical URL), or None."""
    params = {
        "action": "query",
        "format": "json",
        "formatversion": 2,
        "prop": "extracts",
        "explaintext": 1,
        "exsectionformat": "plain",
        "redirects": 1,
        "titles": requested_title,
    }
    response = client.get(WIKIPEDIA_API, params=params)
    response.raise_for_status()
    payload = response.json()
    pages = payload.get("query", {}).get("pages", [])
    if not pages:
        return None

    page = pages[0]
    extract = re.sub(r"\n{3,}", "\n\n", page.get("extract", "")).strip()
    if page.get("missing") or len(extract) < 250:
        return None

    title = page.get("title", requested_title)
    page_slug = quote(title.replace(" ", "_"), safe="()_'-,")
    url = f"https://en.wikipedia.org/wiki/{page_slug}"
    return title, extract, url


def save_document_metadata(engine, event_id: int, title: str, source_url: str) -> int:
    """Insert or update a document metadata row and return its doc_id."""
    with Session(engine) as db:
        document = db.scalar(select(Document).where(Document.source_url == source_url))
        if document is None:
            document = Document(
                event_id=event_id,
                source_url=source_url,
                title=title,
                content_type="wikipedia_race_report",
                scraped_at=datetime.now(),
            )
            db.add(document)
        else:
            document.event_id = event_id
            document.title = title
            document.content_type = "wikipedia_race_report"
            document.scraped_at = datetime.now()
        db.commit()
        db.refresh(document)
        return document.doc_id


def index_article(engine, collection, event_id: int, event_name: str, season: int,
                  title: str, source_url: str, article_text: str) -> int:
    chunks = chunk_text(article_text)
    if not chunks:
        return 0

    doc_id = save_document_metadata(engine, event_id, title, source_url)
    vectors = embed_texts(chunks)
    chunk_ids = [f"doc-{doc_id}-chunk-{index}" for index in range(len(chunks))]
    metadatas = [
        {
            "doc_id": int(doc_id),
            "event_id": int(event_id),
            "event_name": event_name,
            "season": int(season),
            "title": title,
            "source_url": source_url,
            "chunk_index": int(index),
        }
        for index in range(len(chunks))
    ]

    # Replace previous vectors for this source so re-running ingestion is safe.
    collection.delete(where={"doc_id": int(doc_id)})
    collection.upsert(
        ids=chunk_ids,
        embeddings=vectors,
        documents=chunks,
        metadatas=metadatas,
    )

    with Session(engine) as db:
        db.execute(delete(EmbeddingMetadata).where(EmbeddingMetadata.doc_id == doc_id))
        db.add_all(
            [
                EmbeddingMetadata(
                    doc_id=doc_id,
                    chunk_index=index,
                    chunk_text_preview=chunk[:500],
                    vector_db_id=chunk_ids[index],
                    created_at=datetime.now(),
                )
                for index, chunk in enumerate(chunks)
            ]
        )
        db.commit()

    return len(chunks)


def main() -> None:
    year = int(sys.argv[1]) if len(sys.argv) > 1 else DEFAULT_SEASON
    engine = get_engine()
    collection = get_collection()

    with Session(engine) as db:
        events = db.execute(
            select(Event.event_id, Event.event_name, Season.year)
            .join(Season, Season.season_id == Event.season_id)
            .where(Season.year == year)
            .order_by(Event.round)
        ).all()

    if not events:
        raise SystemExit(f"No events found for season {year}. Load that season into PostgreSQL first.")

    indexed_events = 0
    total_chunks = 0
    with httpx.Client(
        timeout=45.0,
        headers={"User-Agent": USER_AGENT},
        follow_redirects=True,
    ) as client:
        for event in events:
            requested_title = f"{event.year} {event.event_name}".strip()
            print(f"Fetching: {requested_title}")
            try:
                article = fetch_wikipedia_article(client, requested_title)
            except httpx.HTTPError as exc:
                print(f"  ERROR: Wikipedia request failed: {exc}")
                time.sleep(0.5)
                continue

            if article is None:
                print("  SKIP: no sufficiently long article found for this title")
                time.sleep(0.5)
                continue

            title, article_text, source_url = article
            try:
                chunk_count = index_article(
                    engine=engine,
                    collection=collection,
                    event_id=event.event_id,
                    event_name=event.event_name,
                    season=event.year,
                    title=title,
                    source_url=source_url,
                    article_text=article_text,
                )
            except Exception as exc:
                print(f"  ERROR while indexing {title}: {exc}")
                time.sleep(0.5)
                continue

            if chunk_count:
                indexed_events += 1
                total_chunks += chunk_count
                print(f"  INDEXED: {chunk_count} chunks | {source_url}")
            time.sleep(0.5)  # Be polite to Wikipedia's public API.

    print("\nIngestion complete")
    print(f"Season: {year}")
    print(f"Race articles indexed: {indexed_events}/{len(events)}")
    print(f"Chunks indexed in this run: {total_chunks}")
    print(f"Total Chroma chunks currently stored: {collection.count()}")
    if indexed_events == 0:
        print("No documents were indexed. Check the event names and Wikipedia article titles.")


if __name__ == "__main__":
    main()
