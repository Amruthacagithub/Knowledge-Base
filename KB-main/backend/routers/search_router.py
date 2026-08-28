"""
Search router — main search/ask endpoint.
"""
import time
from fastapi import APIRouter, HTTPException, Header
from pydantic import BaseModel

from backend.services.auth import authenticate
from backend.services.retriever import hybrid_search
from backend.services.reranker import rerank
from backend.services.generator import generate_answer
from backend.services.audit import log_search

router = APIRouter(prefix="/api", tags=["search"])


class SearchRequest(BaseModel):
    query: str
    department_filter: str | None = None


class CitationItem(BaseModel):
    marker: int
    doc_title: str
    doc_id: str
    department: str
    chunk_text: str
    page_start: int | None = None
    page_end: int | None = None
    file_type: str = "markdown"


class SearchResponse(BaseModel):
    answer: str
    citations: list[CitationItem]
    latency_ms: int
    chunks_found: int
    query_type: str
    departments_hit: list[str] = []


@router.post("/search", response_model=SearchResponse)
def search(req: SearchRequest, authorization: str = Header(...)):
    """
    Search the knowledge base and get an AI-generated answer.

    Requires a Bearer token from the login endpoint.
    """
    start = time.time()

    # Authenticate
    token = authorization.replace("Bearer ", "")
    user_ctx = authenticate(token)
    if not user_ctx:
        raise HTTPException(status_code=401, detail="Invalid or expired token")

    # Search
    candidates, query_type = hybrid_search(
        query=req.query,
        user_ctx=user_ctx,
        department_filter=req.department_filter,
    )

    if not candidates:
        elapsed_ms = int((time.time() - start) * 1000)
        return SearchResponse(
            answer=(
                "I couldn't find any relevant documents matching your question. "
                "Try different keywords, remove the department filter, or check that "
                "you have access to the content you're looking for."
            ),
            citations=[],
            latency_ms=elapsed_ms,
            chunks_found=0,
            query_type=query_type,
            departments_hit=[],
        )

    # Rerank
    ranked = rerank(query=req.query, candidates=candidates, top_n=8)

    # Generate answer
    result = generate_answer(question=req.query, ranked_chunks=ranked)

    departments_hit = sorted(set(r.get("department", "") for r in ranked if r.get("department")))

    # Audit log
    doc_ids = list(set(r.get("doc_id", "") for r in ranked))
    log_search(
        user_id=user_ctx.user_id,
        query_text=req.query,
        doc_ids=doc_ids,
        allowed=True,
    )

    elapsed_ms = int((time.time() - start) * 1000)

    return SearchResponse(
        answer=result["answer"],
        citations=[CitationItem(**c) for c in result["citations"]],
        latency_ms=elapsed_ms,
        chunks_found=len(candidates),
        query_type=query_type,
        departments_hit=departments_hit,
    )
