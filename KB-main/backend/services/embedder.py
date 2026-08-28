"""
Embedding service — encodes text chunks and upserts into Qdrant.
"""
from sentence_transformers import SentenceTransformer
from qdrant_client import QdrantClient
from qdrant_client.models import (
    Distance, VectorParams, PointStruct, Filter,
    FieldCondition, MatchValue, PayloadSchemaType,
)
import uuid

from backend.config import (
    QDRANT_URL,
    QDRANT_API_KEY,
    QDRANT_HOST,
    QDRANT_PORT,
    QDRANT_COLLECTION,
    EMBEDDING_MODEL,
    EMBEDDING_DIM,
)

# ── Singletons (loaded once, reused) ──
_model = None
_client = None


def get_embedding_model() -> SentenceTransformer:
    global _model
    if _model is None:
        print(f"  Loading embedding model: {EMBEDDING_MODEL} ...")
        _model = SentenceTransformer(EMBEDDING_MODEL)
    return _model


def get_qdrant_client() -> QdrantClient:
    global _client
    if _client is None:
        if QDRANT_URL:
            _client = QdrantClient(
                url=QDRANT_URL,
                api_key=QDRANT_API_KEY or None,
                check_compatibility=False,
            )
            label = QDRANT_URL if len(QDRANT_URL) <= 48 else f"{QDRANT_URL[:45]}…"
            print(f"  Qdrant client: cloud ({label})")
        else:
            _client = QdrantClient(host=QDRANT_HOST, port=QDRANT_PORT)
            print(f"  Qdrant client: {QDRANT_HOST}:{QDRANT_PORT}")
    return _client


def ensure_payload_indexes():
    """Keyword indexes required for RBAC filters on Qdrant Cloud."""
    client = get_qdrant_client()
    for field in ("access_roles", "department", "classification"):
        try:
            client.create_payload_index(
                collection_name=QDRANT_COLLECTION,
                field_name=field,
                field_schema=PayloadSchemaType.KEYWORD,
            )
            print(f"  Created payload index: {field}")
        except Exception as exc:
            msg = str(exc).lower()
            if "already exists" in msg or "already has" in msg:
                continue
            print(f"  Payload index {field}: {exc}")


def ensure_collection():
    """Create the Qdrant collection if it doesn't exist."""
    client = get_qdrant_client()
    collections = [c.name for c in client.get_collections().collections]
    if QDRANT_COLLECTION not in collections:
        client.create_collection(
            collection_name=QDRANT_COLLECTION,
            vectors_config=VectorParams(
                size=EMBEDDING_DIM,
                distance=Distance.COSINE,
            ),
        )
        print(f"  Created Qdrant collection: {QDRANT_COLLECTION}")
    else:
        print(f"  Qdrant collection already exists: {QDRANT_COLLECTION}")
    ensure_payload_indexes()


def _chunk_texts(chunks: list) -> list[dict]:
    """Normalize chunks as list of dicts with text and page fields."""
    out = []
    for c in chunks:
        if isinstance(c, dict):
            out.append(c)
        else:
            out.append({"text": c, "page_start": 1, "page_end": 1})
    return out


def embed_and_upsert(
    chunks: list,
    doc_id: str,
    doc_title: str,
    department: str,
    classification: str,
    file_type: str = "markdown",
) -> int:
    """
    Embed text chunks and upsert them into Qdrant.

    Returns:
        Number of points upserted.
    """
    chunk_dicts = _chunk_texts(chunks)
    if not chunk_dicts:
        return 0

    model = get_embedding_model()
    client = get_qdrant_client()

    texts = [c["text"] for c in chunk_dicts]
    vectors = model.encode(texts, show_progress_bar=False).tolist()

    # Build access_roles list based on classification + department
    if classification == "public":
        access_roles = ["Employee", "HR", "Engineer", "Sales", "Admin"]
    else:
        # restricted: only the department's role + admin
        access_roles = [department_to_role(department), "Admin"]

    # Create points
    points = []
    for i, (chunk, vector) in enumerate(zip(chunk_dicts, vectors)):
        point_id = str(uuid.uuid4())
        points.append(
            PointStruct(
                id=point_id,
                vector=vector,
                payload={
                    "text": chunk["text"],
                    "doc_id": doc_id,
                    "doc_title": doc_title,
                    "department": department,
                    "classification": classification,
                    "access_roles": access_roles,
                    "chunk_index": i,
                    "page_start": chunk.get("page_start", 1),
                    "page_end": chunk.get("page_end", 1),
                    "file_type": file_type,
                },
            )
        )

    # Upsert in batches of 64
    batch_size = 64
    for start in range(0, len(points), batch_size):
        batch = points[start : start + batch_size]
        client.upsert(collection_name=QDRANT_COLLECTION, points=batch)

    return len(points)


def department_to_role(department: str) -> str:
    """Map department name to role name."""
    mapping = {
        "HR": "HR",
        "Engineering": "Engineer",
        "Sales": "Sales",
    }
    return mapping.get(department, "Employee")


def vector_search(
    query: str,
    qdrant_filter: Filter | None = None,
    top_k: int = 20,
) -> list[dict]:
    """
    Search Qdrant for chunks similar to the query.

    Returns:
        List of dicts with text, doc_id, doc_title, department, score.
    """
    model = get_embedding_model()
    client = get_qdrant_client()

    query_vector = model.encode(query).tolist()

    results = client.query_points(
        collection_name=QDRANT_COLLECTION,
        query=query_vector,
        query_filter=qdrant_filter,
        limit=top_k,
        with_payload=True,
    )

    return [
        {
            "text": hit.payload["text"],
            "doc_id": hit.payload["doc_id"],
            "doc_title": hit.payload["doc_title"],
            "department": hit.payload["department"],
            "classification": hit.payload.get("classification", "public"),
            "chunk_index": hit.payload.get("chunk_index", 0),
            "page_start": hit.payload.get("page_start", 1),
            "page_end": hit.payload.get("page_end", 1),
            "file_type": hit.payload.get("file_type", "markdown"),
            "score": hit.score,
            "source": "vector",
        }
        for hit in results.points
    ]
