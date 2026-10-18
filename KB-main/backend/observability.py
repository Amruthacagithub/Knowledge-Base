"""
Observability module for Knowledge Base.
Provides:
- Structured logging with correlation IDs (X-Request-ID).
- Prometheus metrics collectors (request count, latency histogram, search queries).
- Prometheus /metrics exposition endpoint.
"""
import time
import uuid
import logging
import json
from datetime import datetime, timezone
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware

# Initialize Logger
logger = logging.getLogger("knowledge_base.access")
if not logger.handlers:
    handler = logging.StreamHandler()
    formatter = logging.Formatter('%(message)s')
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    logger.setLevel(logging.INFO)

# Prometheus Metrics Setup
try:
    from prometheus_client import Counter, Histogram, Gauge, generate_latest, CONTENT_TYPE_LATEST
    PROMETHEUS_AVAILABLE = True

    HTTP_REQUESTS_TOTAL = Counter(
        "knowledge_base_http_requests_total",
        "Total count of HTTP requests processed by Knowledge Base",
        ["method", "endpoint", "status"]
    )
    HTTP_REQUEST_DURATION_SECONDS = Histogram(
        "knowledge_base_http_request_duration_seconds",
        "Histogram of HTTP request latency in seconds",
        ["method", "endpoint"],
        buckets=(0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0, 10.0)
    )
    SEARCH_QUERIES_TOTAL = Counter(
        "knowledge_base_search_queries_total",
        "Total search queries processed by the RAG hybrid pipeline",
        ["query_type"]
    )
    COMPONENT_HEALTH_GAUGE = Gauge(
        "knowledge_base_component_health",
        "Component health status (1 for up, 0 for down)",
        ["component"]
    )
except ImportError:
    PROMETHEUS_AVAILABLE = False


class ObservabilityMiddleware(BaseHTTPMiddleware):
    """Middleware for structured request logging and Prometheus metrics collection."""

    async def dispatch(self, request: Request, call_next):
        # Extract or generate correlation ID
        request_id = request.headers.get("X-Request-ID") or str(uuid.uuid4())
        request.state.request_id = request_id
        
        start_time = time.time()
        path = request.url.path
        method = request.method

        try:
            response = await call_next(request)
            status_code = response.status_code
        except Exception as exc:
            status_code = 500
            duration = time.time() - start_time
            self._log_request(request_id, method, path, status_code, duration, str(exc))
            raise exc

        duration = time.time() - start_time
        response.headers["X-Request-ID"] = request_id

        # Skip recording prometheus metrics for /metrics itself to prevent scrape amplification
        if path != "/metrics":
            self._log_request(request_id, method, path, status_code, duration)
            if PROMETHEUS_AVAILABLE:
                # Sanitize endpoint path for metrics to avoid high cardinality
                endpoint = self._sanitize_path(path)
                HTTP_REQUESTS_TOTAL.labels(method=method, endpoint=endpoint, status=str(status_code)).inc()
                HTTP_REQUEST_DURATION_SECONDS.labels(method=method, endpoint=endpoint).observe(duration)

        return response

    @staticmethod
    def _sanitize_path(path: str) -> str:
        """Collapse dynamic parameters into static metric labels."""
        if path.startswith("/api/documents/") and path.endswith("/file"):
            return "/api/documents/{id}/file"
        if path.startswith("/api/documents/"):
            return "/api/documents/{id}"
        return path

    @staticmethod
    def _log_request(request_id: str, method: str, path: str, status: int, duration: float, error: str = None):
        """Emit structured JSON access log."""
        log_entry = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "request_id": request_id,
            "method": method,
            "path": path,
            "status": status,
            "latency_ms": round(duration * 1000, 2),
        }
        if error:
            log_entry["error"] = error
        logger.info(json.dumps(log_entry))


def record_search_query(query_type: str):
    """Record business metric for executed search query."""
    if PROMETHEUS_AVAILABLE:
        SEARCH_QUERIES_TOTAL.labels(query_type=query_type or "unknown").inc()


def update_component_health(component: str, is_up: bool):
    """Update health gauge for monitoring dependency availability."""
    if PROMETHEUS_AVAILABLE:
        COMPONENT_HEALTH_GAUGE.labels(component=component).set(1 if is_up else 0)


def get_metrics_response() -> Response:
    """Return scraped Prometheus metrics payload."""
    if not PROMETHEUS_AVAILABLE:
        return Response(content="# Prometheus client not installed\n", media_type="text/plain")
    return Response(content=generate_latest(), media_type=CONTENT_TYPE_LATEST)

