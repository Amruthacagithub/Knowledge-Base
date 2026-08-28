"""
EKIP — Enterprise Knowledge Intelligence Platform

FastAPI application entry point.
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend.config import CORS_ORIGINS
from backend.routers.auth_router import router as auth_router
from backend.routers.search_router import router as search_router
from backend.routers.documents_router import router as documents_router

app = FastAPI(
    title="Knowledge Base",
    description="Internal document search with AI-powered answers and role-based access.",
    version="0.2.0",
)

# CORS — localhost in dev; set CORS_ORIGINS in production (include your Vercel URL)
_cors_origins = [o.strip() for o in CORS_ORIGINS.split(",") if o.strip()]
app.add_middleware(
    CORSMiddleware,
    allow_origins=_cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(auth_router)
app.include_router(search_router)
app.include_router(documents_router)


def _check_postgres() -> bool:
    try:
        from backend.database import SessionLocal
        db = SessionLocal()
        from sqlalchemy import text
        db.execute(text("SELECT 1"))
        db.close()
        return True
    except Exception:
        return False


def _check_qdrant() -> bool:
    try:
        from backend.services.embedder import get_qdrant_client
        from backend.config import QDRANT_COLLECTION
        client = get_qdrant_client()
        client.get_collection(QDRANT_COLLECTION)
        return True
    except Exception:
        return False


@app.get("/api/health")
def health_check():
    """Health check with dependency status."""
    pg_ok = _check_postgres()
    qd_ok = _check_qdrant()
    status = "ok" if pg_ok and qd_ok else "degraded"
    return {
        "status": status,
        "service": "knowledge-base",
        "components": {
            "postgres": "up" if pg_ok else "down",
            "qdrant": "up" if qd_ok else "down",
        },
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "backend.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        reload_excludes=["frontend/node_modules/*", "frontend/dist/*", "indexdir/*"],
    )
