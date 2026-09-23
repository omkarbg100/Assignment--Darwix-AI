"""
Q2 - Arogya Shield Plus Knowledge Base: Ingestion Pipeline
Loads mock JSON dataset → cleans → embeds → stores in ChromaDB
"""

import json
import os
import re
from pathlib import Path
from typing import Optional

import chromadb
try:
    from chromadb.utils.embedding_functions import SentenceTransformerEmbeddingFunction
except ImportError:
    SentenceTransformerEmbeddingFunction = None
from chromadb.utils.embedding_functions import DefaultEmbeddingFunction

# ── Config ────────────────────────────────────────────────────────────────────
DATA_PATH = Path(__file__).parent / "data" / "arogya_shield_plus.json"
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

# ── PII patterns (presidio-lite style — regex fallback) ───────────────────────
PII_PATTERNS = [
    (r"\b\d{10}\b", "[PHONE_REDACTED]"),          # 10-digit phone numbers
    (r"\b[A-Z]{5}\d{4}[A-Z]\b", "[PAN_REDACTED]"),  # PAN card
    (r"\b\d{12}\b", "[AADHAAR_REDACTED]"),         # Aadhaar
    (r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}", "[EMAIL_REDACTED]"),
]


def clean_text(text: str) -> str:
    """Remove extra whitespace and apply PII redaction."""
    # Normalize whitespace
    text = re.sub(r"\s+", " ", text).strip()
    # Redact PII
    for pattern, replacement in PII_PATTERNS:
        text = re.sub(pattern, replacement, text)
    return text


def build_document(record: dict) -> tuple[str, dict]:
    """Return (cleaned_content, metadata) for a KB record."""
    content = clean_text(record["content"])
    metadata = {
        "record_id": record["record_id"],
        "title": record["title"],
        "category": record["category"],
        "source": record["source"],
        "version": str(record.get("version", "1.0")),
        "pii": str(record.get("pii", False)),
        "chunk_index": int(record.get("chunk_index", 0)),
        "parent_doc": record.get("parent_doc", ""),
        "last_updated": record.get("last_updated", ""),
    }
    return content, metadata


def ingest(dry_run: bool = False) -> int:
    """
    Main ingestion function.
    Returns the number of records successfully indexed.
    """
    # Load dataset
    with open(DATA_PATH, encoding="utf-8") as f:
        records = json.load(f)
    print(f"[ingest] Loaded {len(records)} records from {DATA_PATH}")

    # Validate and clean
    cleaned_docs = []
    for rec in records:
        required_fields = ["record_id", "title", "content", "category", "source"]
        missing = [f for f in required_fields if not rec.get(f)]
        if missing:
            print(f"[WARN] Skipping {rec.get('record_id', 'UNKNOWN')} — missing: {missing}")
            continue
        if not rec.get("content", "").strip():
            print(f"[WARN] Skipping {rec['record_id']} — empty content")
            continue
        cleaned_docs.append(rec)

    print(f"[ingest] {len(cleaned_docs)} records passed validation")

    if dry_run:
        print("[ingest] Dry run — skipping ChromaDB write")
        return len(cleaned_docs)

    # Set up ChromaDB
    CHROMA_PATH.mkdir(parents=True, exist_ok=True)
    client = chromadb.PersistentClient(path=str(CHROMA_PATH))

    # Use local SentenceTransformer or ONNX embeddings — no API key required
    print(f"[ingest] Loading local embedding model: {EMBEDDING_MODEL} ...")
    local_ef = get_embedding_function()

    # Create or get collection (reset if re-running)
    try:
        client.delete_collection(COLLECTION_NAME)
        print(f"[ingest] Deleted existing collection '{COLLECTION_NAME}'")
    except Exception:
        pass

    collection = client.create_collection(
        name=COLLECTION_NAME,
        embedding_function=local_ef,
        metadata={"hnsw:space": "cosine"},
    )
    print(f"[ingest] Created collection '{COLLECTION_NAME}'")

    # Batch upsert
    BATCH_SIZE = 10
    total_indexed = 0
    for i in range(0, len(cleaned_docs), BATCH_SIZE):
        batch = cleaned_docs[i : i + BATCH_SIZE]
        ids, documents, metadatas = [], [], []
        for rec in batch:
            content, metadata = build_document(rec)
            ids.append(rec["record_id"])
            documents.append(content)
            metadatas.append(metadata)

        collection.upsert(ids=ids, documents=documents, metadatas=metadatas)
        total_indexed += len(batch)
        print(f"[ingest] Indexed {total_indexed}/{len(cleaned_docs)} records")

    print(f"\n[ingest] [SUCCESS] Done -- {total_indexed} records in ChromaDB at {CHROMA_PATH}")
    return total_indexed


if __name__ == "__main__":
    ingest()
