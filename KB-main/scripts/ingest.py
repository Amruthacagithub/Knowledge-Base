"""
Ingestion script — parse, chunk, embed, and index all documents.
Run: python scripts/ingest.py
"""
import sys
import json
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from backend.config import DOCUMENTS_DIR
from backend.services.embedder import ensure_collection
from backend.services.bm25_index import create_bm25_index
from backend.services.ingest_service import ingest_document_entry
from backend.database import SessionLocal


def load_manifest() -> list[dict]:
    manifest_path = DOCUMENTS_DIR / "manifest.json"
    if not manifest_path.exists():
        print(f"ERROR: manifest.json not found at {manifest_path}")
        sys.exit(1)
    return json.loads(manifest_path.read_text(encoding="utf-8"))


def ingest_all():
    print("=== EKIP Document Ingestion ===\n")

    manifest = load_manifest()
    print(f"Found {len(manifest)} documents in manifest.\n")

    ensure_collection()
    create_bm25_index()

    db = SessionLocal()
    total_chunks = 0
    success_count = 0

    try:
        for entry in manifest:
            print(f"  [{entry['department']}] {entry['title']}")
            try:
                result = ingest_document_entry(entry, DOCUMENTS_DIR, db=db)
                print(
                    f"    → {result['chunks_indexed']} chunks "
                    f"({result['file_type']}) → Qdrant + BM25"
                )
                total_chunks += result["chunks_indexed"]
                success_count += 1
            except FileNotFoundError as e:
                print(f"    ⚠ {e}, skipping.")
            except Exception as e:
                print(f"    ⚠ Error: {e}, skipping.")
            print()
    finally:
        db.close()

    print(
        f"=== Done! Ingested {success_count}/{len(manifest)} documents, "
        f"{total_chunks} chunks total. ==="
    )


if __name__ == "__main__":
    ingest_all()
