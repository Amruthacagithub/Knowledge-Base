"""
EKIP — Enterprise Knowledge Intelligence Platform

FastAPI application entry point.
"""
from fastapi import FastAPI, status
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware

from backend.config import CORS_ORIGINS, APP_VERSION, COMMIT_SHA, ENVIRONMENT
from backend.observability import ObservabilityMiddleware, get_metrics_response, update_component_health
from backend.routers.auth_router import router as auth_router
from backend.routers.search_router import router as search_router
from backend.routers.documents_router import router as documents_router

app = FastAPI(
    title="Knowledge Base",
    description="Internal document search with AI-powered answers and role-based access.",
    version=APP_VERSION,
)

# Observability middleware (request correlation ID, JSON access logs, Prometheus metrics)
app.add_middleware(ObservabilityMiddleware)

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


@app.get("/metrics", tags=["observability"])
def metrics():
    """Prometheus metrics scrape endpoint."""
    return get_metrics_response()


@app.get("/api/version", tags=["system"])
def version_info():
    """Build and release version metadata."""
    return {
        "service": "knowledge-base",
        "version": APP_VERSION,
        "commit_sha": COMMIT_SHA,
        "environment": ENVIRONMENT,
        "status": "healthy",
    }


@app.get("/api/health/live", tags=["health"])
def liveness_probe():
    """Kubernetes liveness probe — checks that the process is running and event loop is responsive."""
    return {"status": "ok", "service": "knowledge-base"}


@app.get("/api/health/ready", tags=["health"])
def readiness_probe():
    """Kubernetes readiness probe — verifies critical datastore dependencies before routing traffic."""
    pg_ok = _check_postgres()
    qd_ok = _check_qdrant()
    update_component_health("postgres", pg_ok)
    update_component_health("qdrant", qd_ok)

    if pg_ok and qd_ok:
        return {
            "status": "ready",
            "components": {"postgres": "up", "qdrant": "up"},
        }
    return JSONResponse(
        status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
        content={
            "status": "not_ready",
            "components": {
                "postgres": "up" if pg_ok else "down",
                "qdrant": "up" if qd_ok else "down",
            },
        },
    )


@app.get("/api/health/startup", tags=["health"])
def startup_probe():
    """Kubernetes startup probe — verifies initial application initialization."""
    return {"status": "started", "service": "knowledge-base"}


@app.get("/api/health", tags=["health"])
def health_check():
    """Backward-compatible health check with dependency status."""
    pg_ok = _check_postgres()
    qd_ok = _check_qdrant()
    status_str = "ok" if pg_ok and qd_ok else "degraded"
    return {
        "status": status_str,
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
