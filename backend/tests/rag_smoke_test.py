"""Manual smoke test for the local embedding model and Chroma retrieval.

Run from the backend directory after indexing documents:
    ../.venv/bin/python tests/rag_smoke_test.py
"""
from rag.embeddings import embed_texts
from rag.retriever import retrieve_context
from rag.vector_store import get_collection


def main() -> None:
    collection = get_collection()
    print(f"Chroma chunk count: {collection.count()}")
    if collection.count() == 0:
        raise SystemExit("No chunks found. Run: python -m rag.ingest_documents 2023")

    vector = embed_texts(["Why did Ferrari struggle strategically at the 2023 Singapore Grand Prix?"])[0]
    assert vector and isinstance(vector[0], float), "Embedding test failed"
    results = retrieve_context("Why did Ferrari struggle strategically at the 2023 Singapore Grand Prix?", top_k=5)
    assert results, "Retrieval returned no results"

    print("\nTop retrieved passages:")
    for index, result in enumerate(results, start=1):
        metadata = result["metadata"]
        print(f"\n{index}. {metadata.get('title')} | distance={result.get('distance')}")
        print(f"   {metadata.get('source_url')}")
        print(f"   {result['text'][:350]}...")

    print("\nRAG retrieval smoke test passed.")


if __name__ == "__main__":
    main()
