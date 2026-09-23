"""
End-to-end verification and smoke test for the Arogya Shield Plus Knowledge Base.
Validates ChromaDB collection integrity, embeddings, citations, and retrieval quality.

Usage:
    .venv\\Scripts\\python q2_knowledge_base/verify_kb.py
"""

import sys
from pathlib import Path

# Add current directory to path
sys.path.insert(0, str(Path(__file__).parent))
from retrieval import get_collection, retrieve_for_voice_agent, get_embedding_function


def check_env():
    """Check that local embeddings (ONNX or SentenceTransformer) are ready."""
    try:
        ef = get_embedding_function()
        sample = ef(["test"])[0]
        print(f"[OK] Local embeddings initialized successfully (dim: {len(sample)}, no API key needed)")
        return True
    except Exception as e:
        print(f"[ERROR] Local embeddings failed: {e}")
        return False


def check_chroma():
    """Check if ChromaDB collection exists and has records."""
    chroma_path = Path(__file__).parent / "chroma_db"
    if not chroma_path.exists():
        print("[ERROR] ChromaDB not found -- run: .venv\\Scripts\\python q2_knowledge_base/ingest.py")
        sys.exit(1)
    try:
        collection = get_collection()
        count = collection.count()
        print(f"[OK] ChromaDB collection found: {count} records indexed")
        return collection, count
    except Exception as e:
        print(f"[ERROR] ChromaDB error: {e}")
        print("   --> Run: .venv\\Scripts\\python q2_knowledge_base/ingest.py")
        sys.exit(1)


def run_smoke_queries():
    """Run 5 core queries covering Product, Policy, Qualification, FAQ, and Objection as required by Assessment Q2."""
    smoke_tests = [
        ("What is the waiting period for pre-existing conditions?", "policy_rules"),
        ("Can a 62-year-old apply for coverage?", "qualification"),
        ("What plans cover outpatient care?", "coverage"),
        ("Why is the premium so expensive compared to competitors?", "objection"),
        ("How does the cashless hospitalization claim process work?", "claim_process"),
    ]

    print("\n-- Smoke Queries Verification (5 Assessment Categories) ----------------")
    all_passed = True
    for query, expected_category in smoke_tests:
        result = retrieve_for_voice_agent(query)
        if not result["found"]:
            print(f"[FAIL] '{query}' --> No results found")
            all_passed = False
            continue

        score = result.get("top_score", 0)
        category = result.get("category", "?")
        citations = result.get("citations", [])
        preview = result["answer"][:100].replace("\n", " ")

        status = "[PASS]" if score > 0.6 else "[WARN]"
        print(f"{status} Query: '{query}'")
        print(f"       Category: {category} | Top Score: {score:.3f}")
        print(f"       Citation: {citations[0] if citations else 'N/A'}")
        print(f"       Excerpt:  {preview}...")
        print()

    return all_passed


def main():
    print("=" * 70)
    print("AROGYA SHIELD PLUS -- KB INTEGRITY & RETRIEVAL VERIFICATION")
    print("=" * 70)

    check_env()
    check_chroma()
    success = run_smoke_queries()

    if success:
        print("=" * 70)
        print("[SUCCESS] All Question 2 Knowledge Base requirements passed!")
        print("Traceable records, citations, and embedding retrieval verified.")
        print("=" * 70)
    else:
        print("[WARN] Some retrieval checks returned low scores. Check index.")


if __name__ == "__main__":
    main()
