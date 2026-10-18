# Observability & Reliability Architecture: Knowledge Base Platform

## 1. Observability Strategy & Pillars

The Knowledge Base observability framework provides actionable, real-time insights into application performance, RAG search query latency, component health, and user access patterns. It is structured around the core SRE tenets of structured logging, dimensional metrics, health probing, and reliability targets (SLOs).

---

## 2. Health Probing Architecture

To prevent premature container restarts during neural model loading while ensuring rapid failure detection in production, the application separates health into three distinct endpoints:

| Endpoint | Probe Type | Kubernetes Purpose | Success Condition | Failure Behavior |
|---|---|---|---|---|
| `/api/health/startup` | **Startup Probe** | Verifies FastAPI process initialization and ASGI server binding. | HTTP 200 `{"status": "started"}` | Container killed and restarted if not responsive within 60s (`failureThreshold: 12`, `periodSeconds: 5`). |
| `/api/health/live` | **Liveness Probe** | Detects deadlocks, event-loop starvation, or unhandled fatal process hangs. | HTTP 200 `{"status": "ok"}` | If unresponsive for 3 consecutive checks, Kubernetes restarts the pod. |
| `/api/health/ready` | **Readiness Probe** | Validates connectivity to critical datastores (PostgreSQL `SELECT 1` and Qdrant collection status). | HTTP 200 `{"status": "ready"}` | If either datastore is down, returns HTTP 503 `{"status": "not_ready"}`. Kubernetes immediately pulls the pod from the Service endpoint pool without restarting it. |
| `/api/health` | **General Diagnostic** | Backward-compatible endpoint for humans and external load balancers. | HTTP 200 `status: ok` (or `degraded`) | Returns detailed component status JSON. |

---

## 3. Structured Logging & Correlation

### Implementation Details:
- Implemented in [`backend/observability.py`](../../KB-main/backend/observability.py) via `ObservabilityMiddleware`.
- Automatically attaches or extracts a correlation header `X-Request-ID`.
- Every incoming request produces a single, structured JSON log record to `stdout` upon completion.

### Sample Structured Log Record:
```json
{
  "timestamp": "2026-10-18T13:24:22.184310+00:00",
  "request_id": "c71a39f0-3f41-45da-9c44-df9b47e2474a",
  "method": "POST",
  "path": "/api/search",
  "status": 200,
  "latency_ms": 342.15
}
```

### Security & Privacy Protections in Logs:
- **Zero Secret Leakage:** Passwords, Bearer JWTs, and Gemini API keys are never printed to console logs.
- **Payload Privacy:** Search queries and raw document text are excluded from the HTTP access log; business audit records are safely sequestered in the PostgreSQL `access_audit_log` table accessible only to administrators.

---

## 4. Dimensional Metrics & Prometheus Exposition

The backend exposes native Prometheus metrics at `/metrics` using standard exposition formatting:

```text
# HELP knowledge_base_http_requests_total Total count of HTTP requests processed by Knowledge Base
# TYPE knowledge_base_http_requests_total counter
knowledge_base_http_requests_total{endpoint="/api/search",method="POST",status="200"} 42
knowledge_base_http_requests_total{endpoint="/api/documents",method="GET",status="200"} 18
knowledge_base_http_requests_total{endpoint="/api/auth/login",method="POST",status="200"} 5

# HELP knowledge_base_http_request_duration_seconds Histogram of HTTP request latency in seconds
# TYPE knowledge_base_http_request_duration_seconds histogram
knowledge_base_http_request_duration_seconds_bucket{endpoint="/api/search",le="0.1",method="POST"} 12
knowledge_base_http_request_duration_seconds_bucket{endpoint="/api/search",le="0.5",method="POST"} 38
knowledge_base_http_request_duration_seconds_bucket{endpoint="/api/search",le="1.0",method="POST"} 41
knowledge_base_http_request_duration_seconds_sum{endpoint="/api/search",method="POST"} 14.36
knowledge_base_http_request_duration_seconds_count{endpoint="/api/search",method="POST"} 42

# HELP knowledge_base_search_queries_total Total search queries processed by the RAG hybrid pipeline
# TYPE knowledge_base_search_queries_total counter
knowledge_base_search_queries_total{query_type="factual"} 28
knowledge_base_search_queries_total{query_type="keyword"} 14

# HELP knowledge_base_component_health Component health status (1 for up, 0 for down)
# TYPE knowledge_base_component_health gauge
knowledge_base_component_health{component="postgres"} 1
knowledge_base_component_health{component="qdrant"} 1
```

### Metric Cardinality Control:
To prevent memory exhaustion from high-cardinality labels, dynamic URI parameters are sanitized:
- Paths like `/api/documents/doc-12345/file` are collapsed to `/api/documents/{id}/file`.

---

## 5. Grafana Dashboard & PromQL Reference

A pre-packaged Grafana dashboard is supplied at [`monitoring/grafana-dashboard.json`](../../monitoring/grafana-dashboard.json).

### Essential PromQL Alerting Queries:

1. **Request Throughput (RPS):**
   ```promql
   sum(rate(knowledge_base_http_requests_total[1m])) by (status, method)
   ```
2. **P95 Latency by Endpoint:**
   ```promql
   histogram_quantile(0.95, sum(rate(knowledge_base_http_request_duration_seconds_bucket[5m])) by (le, endpoint))
   ```
3. **HTTP 5xx Error Rate:**
   ```promql
   sum(rate(knowledge_base_http_requests_total{status=~"5.."}[5m])) / sum(rate(knowledge_base_http_requests_total[5m])) * 100
   ```
4. **PostgreSQL Down Alert:**
   ```promql
   knowledge_base_component_health{component="postgres"} == 0
   ```

---

## 6. Service Level Objectives (SLOs) & Reliability Targets

| Metric | Service Level Indicator (SLI) | Target (SLO) | Measurement Window |
|---|---|---|---|
| **Availability** | Percentage of non-5xx responses on `/api/search` and `/api/documents`. | **99.5%** | Rolling 24-Hour Window |
| **Search Latency** | 95th percentile response time for hybrid RAG search. | **< 1500 ms** (local) | Rolling 1-Hour Window |
| **Readiness Ratio** | Percentage of backend pods reporting `status: ready`. | **100%** | Instantaneous |

> [!NOTE]
> *Measuring SLOs in a Local Environment:* Local student test environments have bursty single-user traffic and lack long-term statistical stability. SLO targets are defined here to demonstrate enterprise SRE capacity planning and monitoring discipline.

---

## 7. Diagnostic Commands for Live Investigation

```powershell
# 1. Inspect live health status
curl -s http://localhost:8000/api/health | jq .

# 2. Inspect Prometheus metrics
curl -s http://localhost:8000/metrics | grep "knowledge_base"

# 3. View structured JSON access logs from running pods
kubectl logs -l app=backend -n knowledge-base -f --tail=50

# 4. Filter access logs for errors (HTTP status >= 400)
kubectl logs -l app=backend -n knowledge-base --tail=200 | jq 'select(.status >= 400)'
```

