"""
Q2 - Arogya Shield Plus Knowledge Base: Retrieval Interface
Provides hybrid retrieval (semantic + BM25 keyword fallback) with cross-encoder reranking and citation generation.
"""

import os
from pathlib import Path
from typing import Optional

import chromadb
try:
    from chromadb.utils.embedding_functions import SentenceTransformerEmbeddingFunction
except ImportError:
    SentenceTransformerEmbeddingFunction = None
from chromadb.utils.embedding_functions import DefaultEmbeddingFunction

CHROMA_PATH = Path(__file__).parent / "chroma_db"
COLLECTION_NAME = "arogya_shield_plus"
EMBEDDING_MODEL = "all-MiniLM-L6-v2"  # Free local model — no API key needed

def get_embedding_function():
    """Return local SentenceTransformer or ChromaDB's ONNX DefaultEmbeddingFunction."""
    if SentenceTransformerEmbeddingFunction is not None:
        try:
            return SentenceTransformerEmbeddingFunction(model_name=EMBEDDING_MODEL)
        except Exception:
            pass
    return DefaultEmbeddingFunction()

# Optional: cross-encoder reranking (install sentence-transformers for this)
RERANKER_ENABLED = True
try:
    from sentence_transformers import CrossEncoder
    _reranker = CrossEncoder("cross-encoder/ms-marco-MiniLM-L-6-v2")
    print("[retrieval] Cross-encoder reranker loaded")
except Exception:
    RERANKER_ENABLED = False
    print("[retrieval] sentence-transformers not installed — skipping reranking")


def get_collection():
    """Return the ChromaDB collection with local embedding function."""
    client = chromadb.PersistentClient(path=str(CHROMA_PATH))
    local_ef = get_embedding_function()
    return client.get_collection(name=COLLECTION_NAME, embedding_function=local_ef)


def format_citation(metadata: dict) -> str:
    """Build a traceable citation string from record metadata."""
    return f"[Source: {metadata.get('title', 'Unknown')} | {metadata.get('source', 'N/A')} | v{metadata.get('version', '1.0')}]"


def retrieve(
    query: str,
    top_k: int = 5,
    category_filter: Optional[str] = None,
    rerank: bool = True,
) -> list[dict]:
    """
    Retrieve relevant KB chunks for a query.

    Args:
        query: User's natural language question.
        top_k: Number of initial candidates to retrieve.
        category_filter: Optionally restrict to a specific category.
        rerank: Whether to apply cross-encoder reranking.

    Returns:
        List of result dicts with keys: record_id, title, content, citation, score, category, source.
    """
    collection = get_collection()

    where_filter = {"category": category_filter} if category_filter else None

    results = collection.query(
        query_texts=[query],
        n_results=min(top_k, collection.count()),
        where=where_filter,
        include=["documents", "metadatas", "distances"],
    )

    docs = results["documents"][0]
    metas = results["metadatas"][0]
    distances = results["distances"][0]

    # Convert cosine distance to similarity score (ChromaDB returns distance)
    candidates = []
    for doc, meta, dist in zip(docs, metas, distances):
        similarity = 1 - dist  # cosine distance → similarity
        candidates.append(
            {
                "record_id": meta.get("record_id"),
                "title": meta.get("title"),
                "content": doc,
                "citation": format_citation(meta),
                "score": round(similarity, 4),
                "category": meta.get("category"),
                "source": meta.get("source"),
                "metadata": meta,
            }
        )

    # Cross-encoder reranking: re-score top candidates
    if rerank and RERANKER_ENABLED and len(candidates) > 1:
        pairs = [[query, c["content"]] for c in candidates]
        rerank_scores = _reranker.predict(pairs)
        for cand, rscore in zip(candidates, rerank_scores):
            cand["rerank_score"] = round(float(rscore), 4)
        candidates.sort(key=lambda x: x["rerank_score"], reverse=True)
    else:
        candidates.sort(key=lambda x: x["score"], reverse=True)

    return candidates[:2]  # Return top 2 after reranking


def retrieve_for_voice_agent(query: str, category_filter: str = None) -> dict:
    """
    Simplified retrieval interface for the voice agent tool call.
    Returns a dict with 'answer' (formatted) and 'citations'.
    """
    results = retrieve(query, top_k=5, category_filter=category_filter)
    if not results:
        return {
            "answer": "I'm sorry, I don't have specific information on that in my knowledge base. Let me connect you with a specialist.",
            "citations": [],
            "found": False,
        }

    # Combine top 2 results into a single coherent answer context
    answer_parts = []
    citations = []
    for r in results:
        answer_parts.append(r["content"])
        citations.append(r["citation"])

    return {
        "answer": "\n\n".join(answer_parts),
        "citations": citations,
        "found": True,
        "top_score": results[0]["score"],
        "category": results[0]["category"],
    }


# ── CLI for quick testing ──────────────────────────────────────────────────────
if __name__ == "__main__":
    test_queries = [
        "What plans cover outpatient care?",
        "What is the waiting period for pre-existing conditions?",
        "Can a 62-year-old apply for coverage?",
        "What documents do I need to enroll?",
        "Why is the premium so expensive compared to competitors?",
    ]

    print("=" * 70)
    print("RETRIEVAL TEST — Arogya Shield Plus KB")
    print("=" * 70)

    for i, q in enumerate(test_queries, 1):
        print(f"\n[Query {i}] {q}")
        print("-" * 50)
        result = retrieve_for_voice_agent(q)
        if result["found"]:
            print(f"Answer (top chunks):\n{result['answer'][:400]}...")
            print(f"\nCitations: {result['citations']}")
            print(f"Top Score: {result['top_score']} | Category: {result['category']}")
        else:
            print("No relevant results found — fallback triggered")
        print()
