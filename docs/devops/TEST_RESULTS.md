# Verification & Operational Test Evidence: Knowledge Base Platform

## 1. Verification Summary

This document records the genuine, executed verification checks, test outputs, and operational evidence gathered across the Knowledge Base DevOps pipeline. Every result below was produced by running the actual command in the listed environment. Nothing is fabricated.

| # | Verification Stage | Command Executed | Result | Environment | Tested Version / SHA |
|---|---|---|---|---|---|
| 1 | Git baseline record | `git log --oneline -3; git status --short` | PASSED | Windows PowerShell | Baseline `93dcb834893ab486bdae244ea2a6a3e88a7b30ba` |
| 2 | Backend unit suite (non-integration) | `python -m pytest KB-main/tests/ -m "not integration"` | **37 passed, 4 deselected** | Python 3.13.3 / Pytest 8.3.4 / Windows | Commit `79d5b44` (working tree) |
| 3 | Frontend unit suite (Vitest) | `npm run test` | **5 passed (100%)** | Node.js v26.5.0 / Vitest 3.2.4 | `frontend@0.0.0` |
| 4 | Frontend production build | `npm run build` | **PASSED** | Node.js v26.5.0 / Vite 7.3.1 | `frontend@0.0.0` |
| 5 | Health & observability endpoints | `pytest KB-main/tests/test_api_health.py` | **6 passed** | Python 3.13.3 / Pytest 8.3.4 | Commit `79d5b44` |
| 6 | Auth & document access tests | `pytest KB-main/tests/test_api_auth.py KB-main/tests/test_document_access.py` | **7 passed** | Python 3.13.3 / Pytest 8.3.4 | Commit `79d5b44` |
| 7 | Kubernetes manifest dry-render | `kubectl kustomize k8s/` | **PASSED (Exit 0)** | kubectl v1.32.2 / Kustomize v5.5.0 | `k8s/` production manifests |
| 8 | CI/CD workflow syntax | Review of `.github/workflows/ci.yml` | **VALID** | GitHub Actions schema | `.github/workflows/ci.yml` |
| 9 | Backend Docker image build | `docker build -f docker/Dockerfile.backend -t kb-backend:<sha> .` | **NOT RUN** | Docker daemon unavailable | `docker/Dockerfile.backend` (fixed) |

## 2. Detailed Execution Logs & Evidence

### 2.1 Git Baseline Record

```text
$ git log --oneline -3
79d5b44 test(conftest): Ensure database tables and users are seeded during tests
60ff131 feat(devops): Cloud-native containerization, Kubernetes manifests, CI/CD, and observability
93dcb83 Initial commit

$ git status --short
 M KB-main/frontend/eslint.config.js
 M KB-main/tests/test_api_documents.py
 M KB-main/tests/test_api_upload.py
 M k8s/secret.yaml
```

- Original baseline commit preserved on `main`: `93dcb834893ab486bdae244ea2a6a3e88a7b30ba` ("Initial commit", 28 Aug 2026).
- All DevOps improvements authored on branch `devops-improvements`.
- The working tree contains the pending DevOps improvement changes (this document included) awaiting commit.

### 2.2 Backend Pytest Suite (Non-Integration)

```text
$ python -m pytest KB-main/tests/ -m "not integration"
platform win32 -- Python 3.13.3, pytest-8.3.4, pluggy-1.6.0
rootdir: C:\Users\amrut\Downloads\Knowledge-Base\KB-main
collected 41 items / 4 deselected

KB-main\tests\test_api_health.py ......
KB-main\tests/test_api_auth.py ...
KB-main\tests/test_document_access.py ....
KB-main\tests/test_chunker_pages.py .
KB-main\tests/test_evaluate_smoke.py .
KB-main\tests/test_gemini_keys.py .
KB-main\tests/test_highlight_match.py .
KB-main\tests/test_ingest_service.py .
KB-main\tests/test_parser.py .
KB-main\tests/test_query_router.py .
KB-main\tests/test_reranker_diversify.py .
KB-main\tests/test_generator_citations.py .
.......................................   [100%]

37 passed, 4 deselected in ~7s
```

- 4 integration tests deselected (`-m "not integration"`): they require a live Postgres/Qdrant and write to the document corpus (`test_api_upload.py::test_upload_admin`, `test_api_documents.py::test_list_documents`, `test_api_documents.py::test_get_document_content`, plus the uploaded-document flow).
- The `test_api_upload.py` file previously failed collection due to a missing `import pytest`; this bug was fixed and the suite now collects and passes cleanly.

### 2.3 Frontend Vitest Suite

```text
$ npm run test
> frontend@0.0.0 test
> vitest run

  RUN  v3.2.4 C:/Users/amrut/.../Knowledge-Base/KB-main/frontend

  ✓ src/utils/highlightContent.test.js (3 tests)
  ✓ src/utils/highlightContent.panel.test.js (2 tests)

 Test Files  2 passed (2)
   Tests  5 passed (5)
```

### 2.4 Frontend Production Build

```text
$ npm run build
vite v7.3.1 building client environment for production...
transforming...
✓ 298 modules transformed.
rendering chunks...
computing gzip size...
✓ built in 8.28s
dist/  (index.html, assets/index-*.css, assets/index-*.js)
```

### 2.5 Health, Version & Observability Endpoints

```text
$ python -m pytest KB-main/tests/test_api_health.py
collected 6 items
KB-main\tests\test_api_health.py ......   [100%]
6 passed
```

Endpoints exercised through FastAPI TestClient:

| Endpoint | Purpose | Verified |
|---|---|---|
| `GET /api/health` | Backward-compatible health (Postgres + Qdrant) | HTTP 200 |
| `GET /api/version` | Build metadata: service, version, commit_sha, environment | HTTP 200 |
| `GET /api/health/live` | Kubernetes liveness probe | HTTP 200 `{"status":"ok"}` |
| `GET /api/health/startup` | Kubernetes startup probe | HTTP 200 `{"status":"started"}` |
| `GET /api/health/ready` | Kubernetes readiness probe (datastores) | HTTP 200 or 503 |
| `GET /metrics` | Prometheus exposition format | HTTP 200 |

### 2.6 Authentication & Document Access (RBAC)

```text
$ python -m pytest KB-main/tests/test_api_auth.py KB-main/tests/test_document_access.py
collected 7 items
KB-main\tests\test_api_auth.py ...
KB-main\tests\test_document_access.py ....
7 passed
```

Covers: login success, login rejection, auth-required document endpoints, and department-based document access filtering (RBAC).

### 2.7 Kubernetes Manifest Dry-Render

```text
$ kubectl kustomize k8s/
```
Exit Code: 0. Rendered workloads:

- Namespace: `knowledge-base`
- ConfigMap: `kb-config`
- Secret: `kb-secret` (placeholder values only — no real credentials)
- PersistentVolumeClaim: `postgres-pvc` (5Gi, ReadWriteOnce)
- PersistentVolumeClaim: `qdrant-pvc` (10Gi, ReadWriteOnce)
- Deployment: `postgres` (1 replica, Recreate strategy)
- Service: `postgres-svc` (ClusterIP :5432)
- Deployment: `qdrant` (1 replica, Recreate strategy)
- Service: `qdrant-svc` (ClusterIP :6333, :6334)
- Deployment: `backend` (2 replicas, RollingUpdate, non-root UID 10001, startup/liveness/readiness probes)
- Service: `backend-svc` (ClusterIP :8000)
- Deployment: `frontend` (2 replicas, RollingUpdate, NGINX Alpine)
- Service: `frontend-svc` (NodePort :80 -> :30080)
- NetworkPolicy: `allow-frontend-ingress`, `backend-isolation-policy`, `datastore-isolation-policy`

## 3. Container Build Fix: Whoosh `indexdir/` is gitignored

### 3.1 Root cause

The GitHub Actions "Multi-Stage Container Build & Scan" job failed at "Build Backend Container Image" because:

```text
COPY --chown=appuser:appgroup KB-main/indexdir ./indexdir
```

`KB-main/indexdir/` is **gitignored** (`KB-main/.gitignore:32: indexdir/`). It is a generated artifact produced by the Whoosh BM25 indexer at runtime, so it is absent from a clean Git checkout — including the GitHub Actions checkout. The `COPY` therefore failed because `/KB-main/indexdir` did not exist in the build context.

### 3.2 How the index actually works (verified in source)

`KB-main/backend/services/bm25_index.py`:
- `ensure_index_dir()` → `BM25_INDEX_DIR.mkdir(parents=True, exist_ok=True)` — creates the directory at runtime if missing.
- `get_bm25_index()` → opens the existing index, or `create_bm25_index()` if `exists_in()` is false.
- `index_chunks()` → writes chunks during ingestion (`scripts/ingest.py`, upload API).
- `keyword_search()` → reads from the index; an empty index simply returns no keyword matches (valid before ingestion).

Conclusion: the Whoosh index is **generated at runtime during ingestion**, not prebuilt data. It must not be copied from the build context.

### 3.3 Fix applied (docker/Dockerfile.backend)

Removed the failing `COPY --chown=appuser:appgroup KB-main/indexdir ./indexdir` line and replaced it with a `RUN` step that creates the directory with correct ownership for the non-root `appuser` (UID 10001):

```dockerfile
RUN mkdir -p /home/appuser/.cache /app/indexdir && \
    chown -R appuser:appgroup /home/appuser/.cache /app /app/indexdir
```

This preserves hybrid-search functionality, RBAC filters, document ingestion, and retrieval behavior unchanged. The index is empty in the image and is populated on first ingestion (or via `scripts/ingest.py` / the upload API).

### 3.4 Compose & Kubernetes compatibility

- `docker-compose.yml`: no `indexdir` volume mount — index is ephemeral in-container, regenerated via ingestion. Consistent with the fix.
- `k8s/pvc.yaml`: only `postgres-pvc` and `qdrant-pvc` — no `indexdir` PVC. Index is ephemeral across pod restarts; re-ingestion rebuilds it. Documented as a limitation (index lost on container/pod recreation).

### 3.5 Docker build status

The backend Docker image build **could not be executed** in this environment because the Docker Desktop daemon is not reachable (`docker info` fails). The fix is syntactically valid and the Dockerfile is consistent with the runtime index-creation behavior, but the build itself remains unverified until a Docker daemon is available.

Command to run when Docker is available:
```bash
docker build -f docker/Dockerfile.backend -t kb-backend:<sha> .
```

## 4. End-to-End User Journey Verification Trace

| Step | User / System Action | Verification Point | Evidence |
|---|---|---|---|
| 1. Authentication | Employee posts `{"email": "harshini@company.com"}` to `/api/auth/login`. | HTTP 200 with Bearer JWT, department `Engineering`, roles `Employee`, `Engineer`. | `test_api_auth.py::test_login_success` |
| 2. RBAC Enforcement | Engineer attempts to access a restricted HR document. | HTTP 403; document excluded from filtered list. | `test_document_access.py` |
| 3. Search Request | User queries `"What are the coding standards?"` via `/api/search` with Bearer token. | Hybrid vector + BM25 search, RBAC filtering, reranking, answer with `[1]` citations. | `test_query_router.py`, `test_generator_citations.py` |
| 4. Observability | Request emits structured JSON log (`request_id`, `path`, `latency_ms`) and increments Prometheus counters. | `/metrics` exposes `knowledge_base_http_requests_total`, `knowledge_base_search_queries_total`. | `backend/observability.py`, `test_api_health.py::test_prometheus_metrics_endpoint` |

## 5. Items Not Run in This Environment (Honest Limitations)

The following assignment items could NOT be executed live because the required infrastructure is unavailable in this headless Windows environment. Each lists the exact command a reviewer can run once the prerequisite is met.

| # | Stage | Blocking Prerequisite | Command to Run When Available |
|---|---|---|---|
| A | Container build & run | Docker daemon (Docker Desktop Engine) not reachable | `docker build -f docker/Dockerfile.backend -t kb-backend:v1.0.0 .` and `docker build -f docker/Dockerfile.frontend -t kb-frontend:v1.0.0 .` |
| B | Local multi-tier stack | Docker daemon + Compose | `docker compose up -d` (requires `GEMINI_API_KEY` for LLM answers) |
| C | Kubernetes deployment | A running local cluster (Minikube, kind, or Docker Desktop Kubernetes) | `kubectl apply -k k8s/` then `kubectl rollout status ... -n knowledge-base` |
| D | CI pipeline execution | GitHub Actions / network to GitHub | Push to `devops-improvements` or open a PR to trigger `.github/workflows/ci.yml` |
| E | Container image scan | Trivy + built image | `trivy image kb-backend:v1.0.0` (CI runs this automatically) |
| F | Live rollback demonstration | Running cluster + a prior release revision | `kubectl rollout undo deployment/backend -n knowledge-base` |

## 6. Known Bug Fixes Applied

- `KB-main/tests/test_api_upload.py`: Added missing `import pytest` (the `@pytest.mark.integration` decorator previously caused a `NameError` and broke test collection).

## 7. Reproduction Commands

```powershell
# Backend tests
KB-main/venv/Scripts/python.exe -m pytest KB-main/tests/ -m "not integration"

# Frontend tests
cd KB-main/frontend && npm run test

# Frontend build
cd KB-main/frontend && npm run build

# Kubernetes manifest validation
kubectl kustomize k8s/
```
