"""
Documents router — list, read, download, and upload documents.
"""
from pathlib import Path

from fastapi import APIRouter, HTTPException, Header, Query, UploadFile, File, Form
from fastapi.responses import FileResponse
from pydantic import BaseModel

from backend.config import DOCUMENTS_DIR
from backend.database import SessionLocal
from backend.models import Document
from backend.services.auth import authenticate
from backend.services.document_access import user_can_access_document
from backend.services.parser import parse_document
from backend.services.ingest_service import ingest_document_entry, file_type_from_path

router = APIRouter(prefix="/api/documents", tags=["documents"])

MAX_UPLOAD_BYTES = 10 * 1024 * 1024
ALLOWED_EXTENSIONS = {".pdf", ".md", ".txt"}


class DocumentSummary(BaseModel):
    id: str
    title: str
    department: str
    classification: str
    file_path: str
    file_type: str = "markdown"


class DocumentListResponse(BaseModel):
    documents: list[DocumentSummary]
    total: int


class PageSegment(BaseModel):
    page: int
    text: str


class DocumentContentResponse(BaseModel):
    id: str
    title: str
    department: str
    classification: str
    content: str
    file_type: str = "markdown"
    pages: list[PageSegment] = []
    highlight_excerpt: str | None = None
    highlight_excerpts: list[str] = []
    highlight_page: int | None = None


class UploadResponse(BaseModel):
    doc_id: str
    title: str
    chunks_indexed: int
    file_type: str


def _require_user(authorization: str):
    token = authorization.replace("Bearer ", "")
    user_ctx = authenticate(token)
    if not user_ctx:
        raise HTTPException(status_code=401, detail="Invalid or expired token")
    return user_ctx


def _require_admin(user_ctx):
    if "Admin" not in user_ctx.roles:
        raise HTTPException(status_code=403, detail="Admin access required")


def _load_doc_content(doc: Document):
    file_path = DOCUMENTS_DIR / doc.file_path
    if not file_path.exists():
        raise HTTPException(status_code=404, detail="Document file missing on disk")
    segments = parse_document(file_path)
    file_type = file_type_from_path(file_path)
    pages = [PageSegment(page=int(s.get("page", 1)), text=s["text"]) for s in segments]
    content = "\n\n".join(seg["text"] for seg in segments)
    return file_path, file_type, pages, content


def _dedupe_excerpts(highlight: list[str] | None) -> list[str]:
    excerpts = []
    if highlight:
        for h in highlight:
            if h and h.strip():
                excerpts.append(h.strip()[:2000])
    seen = set()
    unique = []
    for e in excerpts:
        key = e[:80]
        if key not in seen:
            seen.add(key)
            unique.append(e)
    return unique


@router.get("", response_model=DocumentListResponse)
def list_documents(authorization: str = Header(...)):
    user_ctx = _require_user(authorization)
    db = SessionLocal()
    try:
        all_docs = db.query(Document).order_by(Document.department, Document.title).all()
        visible = [
            DocumentSummary(
                id=d.id,
                title=d.title,
                department=d.department,
                classification=d.classification,
                file_path=d.file_path,
                file_type=file_type_from_path(DOCUMENTS_DIR / d.file_path),
            )
            for d in all_docs
            if user_can_access_document(d, user_ctx)
        ]
        return DocumentListResponse(documents=visible, total=len(visible))
    finally:
        db.close()


@router.post("/upload", response_model=UploadResponse)
async def upload_document(
    authorization: str = Header(...),
    file: UploadFile = File(...),
    title: str = Form(...),
    department: str = Form(...),
    classification: str = Form(...),
):
    """Admin-only: upload and index a new document."""
    user_ctx = _require_user(authorization)
    _require_admin(user_ctx)

    if classification not in ("public", "restricted"):
        raise HTTPException(status_code=400, detail="classification must be public or restricted")
    if department not in ("HR", "Engineering", "Sales"):
        raise HTTPException(status_code=400, detail="Invalid department")

    suffix = Path(file.filename or "").suffix.lower()
    if suffix not in ALLOWED_EXTENSIONS:
        raise HTTPException(status_code=400, detail="Allowed types: .pdf, .md, .txt")

    data = await file.read()
    if len(data) > MAX_UPLOAD_BYTES:
        raise HTTPException(status_code=400, detail="File too large (max 10 MB)")

    safe_name = "".join(c if c.isalnum() or c in "._-" else "_" for c in (file.filename or "upload"))
    dept_dir = DOCUMENTS_DIR / department.lower()
    dept_dir.mkdir(parents=True, exist_ok=True)
    dest = dept_dir / safe_name
    if dest.exists():
        stem = dest.stem
        dest = dept_dir / f"{stem}_{uuid_hex()}{suffix}"

    dest.write_bytes(data)

    rel_path = str(dest.relative_to(DOCUMENTS_DIR)).replace("\\", "/")
    entry = {
        "path": rel_path,
        "title": title.strip(),
        "department": department,
        "classification": classification,
        "source_id": None,
    }

    _append_manifest(entry)

    db = SessionLocal()
    try:
        result = ingest_document_entry(entry, DOCUMENTS_DIR, db=db)
    except Exception as e:
        dest.unlink(missing_ok=True)
        raise HTTPException(status_code=500, detail=str(e)) from e
    finally:
        db.close()

    return UploadResponse(
        doc_id=result["doc_id"],
        title=result["title"],
        chunks_indexed=result["chunks_indexed"],
        file_type=result["file_type"],
    )


def uuid_hex() -> str:
    import uuid
    return uuid.uuid4().hex[:8]


def _append_manifest(entry: dict):
    import json
    manifest_path = DOCUMENTS_DIR / "manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    manifest.append(entry)
    manifest_path.write_text(json.dumps(manifest, indent=2), encoding="utf-8")


@router.get("/{doc_id}/file")
def download_document_file(doc_id: str, authorization: str = Header(...)):
    """Stream the raw document file (PDF or text source)."""
    user_ctx = _require_user(authorization)
    db = SessionLocal()
    try:
        doc = db.query(Document).filter(Document.id == doc_id).first()
        if not doc:
            raise HTTPException(status_code=404, detail="Document not found")
        if not user_can_access_document(doc, user_ctx):
            raise HTTPException(status_code=403, detail="You do not have access to this document")
        file_path, file_type, _, _ = _load_doc_content(doc)
        media = "application/pdf" if file_type == "pdf" else "text/plain"
        return FileResponse(path=file_path, media_type=media, filename=file_path.name)
    finally:
        db.close()


@router.get("/{doc_id}", response_model=DocumentContentResponse)
def get_document(
    doc_id: str,
    authorization: str = Header(...),
    highlight: list[str] | None = Query(None),
    page: int | None = Query(None, description="Scope highlights to this PDF page"),
):
    user_ctx = _require_user(authorization)
    db = SessionLocal()
    try:
        doc = db.query(Document).filter(Document.id == doc_id).first()
        if not doc:
            raise HTTPException(status_code=404, detail="Document not found")
        if not user_can_access_document(doc, user_ctx):
            raise HTTPException(status_code=403, detail="You do not have access to this document")

        _, file_type, pages, content = _load_doc_content(doc)
        excerpts = _dedupe_excerpts(highlight)

        if page is not None and file_type == "pdf":
            page_text = next((p.text for p in pages if p.page == page), None)
            if page_text and excerpts:
                scoped = []
                for ex in excerpts:
                    if ex in page_text or ex[:80] in page_text:
                        scoped.append(ex)
                    else:
                        scoped.append(ex)
                excerpts = scoped if scoped else excerpts

        return DocumentContentResponse(
            id=doc.id,
            title=doc.title,
            department=doc.department,
            classification=doc.classification,
            content=content,
            file_type=file_type,
            pages=pages if file_type == "pdf" else [],
            highlight_excerpt=excerpts[0] if len(excerpts) == 1 else None,
            highlight_excerpts=excerpts,
            highlight_page=page,
        )
    finally:
        db.close()
