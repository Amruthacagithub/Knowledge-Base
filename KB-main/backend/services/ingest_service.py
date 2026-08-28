"""
Single-document ingestion — shared by CLI ingest and upload API.
"""
import uuid
from pathlib import Path

from backend.database import SessionLocal
from backend.models import Document
from backend.services.parser import parse_document
from backend.services.chunker import chunk_document_segments
from backend.services.embedder import embed_and_upsert
from backend.services.bm25_index import index_chunks


def file_type_from_path(file_path: Path) -> str:
    suffix = file_path.suffix.lower()
    if suffix == ".pdf":
        return "pdf"
    return "markdown"


def ingest_document_entry(
    entry: dict,
    documents_dir: Path,
    db=None,
    *,
    reindex_existing: bool = True,
) -> dict:
    """
    Parse, chunk, embed, and BM25-index one manifest entry.

    entry keys: path, title, department, classification

    Returns:
        {doc_id, title, chunks_indexed, file_type}
    """
    file_path = documents_dir / entry["path"]
    title = entry["title"]
    department = entry["department"]
    classification = entry["classification"]
    file_type = file_type_from_path(file_path)

    if not file_path.exists():
        raise FileNotFoundError(f"File not found: {file_path}")

    segments = parse_document(file_path)
    if not segments:
        raise ValueError(f"No text extracted from {file_path}")

    chunks = chunk_document_segments(segments)
    if not chunks:
        raise ValueError(f"No chunks produced from {file_path}")

    own_db = db is None
    if own_db:
        db = SessionLocal()

    try:
        existing = db.query(Document).filter(Document.title == title).first()
        if existing and reindex_existing:
            doc_id = existing.id
            existing.file_path = str(entry["path"])
            existing.department = department
            existing.classification = classification
            db.commit()
        elif existing:
            doc_id = existing.id
        else:
            doc_id = str(uuid.uuid4())
            doc = Document(
                id=doc_id,
                title=title,
                department=department,
                classification=classification,
                file_path=str(entry["path"]),
            )
            db.add(doc)
            db.commit()

        n_vectors = embed_and_upsert(
            chunks=chunks,
            doc_id=doc_id,
            doc_title=title,
            department=department,
            classification=classification,
            file_type=file_type,
        )
        n_bm25 = index_chunks(
            chunks=chunks,
            doc_id=doc_id,
            doc_title=title,
            department=department,
            classification=classification,
            file_type=file_type,
        )

        return {
            "doc_id": doc_id,
            "title": title,
            "chunks_indexed": len(chunks),
            "vectors_upserted": n_vectors,
            "bm25_indexed": n_bm25,
            "file_type": file_type,
        }
    finally:
        if own_db:
            db.close()
