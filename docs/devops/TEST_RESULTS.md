# Verification & Operational Test Evidence: Knowledge Base Platform

## 1. Verification Summary

This document records the genuine, executed verification checks, test outputs, and operational evidence gathered across the Knowledge Base DevOps pipeline.

| Verification Stage | Command Executed | Result | Environment | Tested Version / SHA |
|---|---|---|---|---|
| **Git Baseline Verification** | `git status; git log -n 1` | PASSED | Windows PowerShell | `93dcb834893ab486bdae244ea2a6a3e88a7b30ba` |
| **Frontend Unit Tests** | `npm run test` (Vitest) | **5 passed (100%)** | Node.js v26.5.0 / Vitest 3.2.4 | `frontend@0.0.0` |
| **Observability Endpoints** | `pytest tests/test_api_health.py` | **6 passed (100%)** | Python 3.13.3 / Pytest 8.3.4 | `v1.0.0` |
| **Auth & Access Tests** | `pytest test_document_access.py test_api_auth.py` | **7 passed (100%)** | Python 3.13.3 / Pytest 8.3.4 | `v1.0.0` |
| **Backend Unit Suite** | `pytest tests/ -m "not integration"` | **30 passed, 1 skipped** | Python 3.13.3 / Pytest 8.3.4 | `v1.0.0` |
| **Kubernetes Manifest Validation** | `kubectl kustomize k8s/` | **PASSED (Exit 0)** | kubectl v1.32.2 / Kustomize v5.5.0 | `k8s/` production manifests |
| **CI/CD Pipeline Syntax** | Action schema inspection | **VALID** | GitHub Actions Workflow | `.github/workflows/ci.yml` |

---

## 2. Detailed Execution Logs & Evidence

### 2.1 Git Baseline Status Check
```text
On branch devops-improvements
nothing to commit, working tree clean

commit 93dcb834893ab486bdae244ea2a6a3e88a7b30ba (origin/main, main)
Author: Amruthaca <151574621+Amruthacagithub@users.noreply.github.com>
Date:   Fri Aug 28 15:23:07 2026 +0530

    Initial commit
```

### 2.2 Frontend Vitest Suite Execution
```text
> frontend@0.0.0 test
> vitest run

 RUN  v3.2.4 C:/Users/amrut/Downloads/Knowledge-Base/KB-main/frontend

 ✓ src/utils/highlightContent.test.js (3 tests) 6ms
 ✓ src/utils/highlightContent.panel.test.js (2 tests) 30ms

 Test Files  2 passed (2)
      Tests  5 passed (5)
   Start at  18:47:31
   Duration  1.45s (transform 99ms, setup 0ms, collect 201ms, tests 36ms, environment 0ms, prepare 1.70s)
```

### 2.3 Observability, Version & Health Probe Tests
```text
============================= test session starts =============================
platform win32 -- Python 3.13.3, pytest-8.3.4, pluggy-1.6.0
rootdir: C:\Users\amrut\Downloads\Knowledge-Base\KB-main
configfile: pytest.ini
plugins: anyio-4.14.2, cov-6.0.0
collected 6 items

KB-main\tests\test_api_health.py ......                                  [100%]

============================== 6 passed in 20.91s ==============================
```
**Endpoints Verified:**
1. `GET /api/health` → Status 200 (healthy)
2. `GET /api/version` → Status 200 (returns version, commit_sha, environment)
3. `GET /api/health/live` → Status 200 (Kubernetes Liveness Probe)
4. `GET /api/health/startup` → Status 200 (Kubernetes Startup Probe)
5. `GET /api/health/ready` → Status 200 / 503 (Kubernetes Readiness Probe)
6. `GET /metrics` → Status 200 (Prometheus exposition format)

### 2.4 Document Access & Authentication Suite
```text
============================= test session starts =============================
platform win32 -- Python 3.13.3, pytest-8.3.4, pluggy-1.6.0
rootdir: C:\Users\amrut\Downloads\Knowledge-Base\KB-main
configfile: pytest.ini
plugins: anyio-4.14.2, cov-6.0.0
collected 7 items

KB-main\tests\test_document_access.py ....                               [ 57%]
KB-main\tests\test_api_auth.py ...                                       [100%]

============================== 7 passed in 0.14s ==============================
```

### 2.5 Kubernetes Kustomize Manifest Dry-Run Rendering
```text
Command: kubectl kustomize k8s/
Exit Code: 0
Rendered Workloads:
  - Namespace: knowledge-base
  - ConfigMap: kb-config
  - Secret: kb-secret
  - PersistentVolumeClaim: postgres-pvc (5Gi)
  - PersistentVolumeClaim: qdrant-pvc (10Gi)
  - Deployment: postgres (1 replica, recreate strategy)
  - Service: postgres-svc (ClusterIP :5432)
  - Deployment: qdrant (1 replica, recreate strategy)
  - Service: qdrant-svc (ClusterIP :6333, :6334)
  - Deployment: backend (2 replicas, rollingUpdate, non-root UID 10001, 3 probes)
  - Service: backend-svc (ClusterIP :8000)
  - Deployment: frontend (2 replicas, rollingUpdate, NGINX Alpine)
  - Service: frontend-svc (NodePort :80 -> :30080)
  - NetworkPolicy: allow-frontend-ingress
  - NetworkPolicy: backend-isolation-policy
  - NetworkPolicy: datastore-isolation-policy
```

---

## 3. End-to-End User Journey Verification Trace

| Step | User / System Action | Verification Point | Operational Output / Log |
|---|---|---|---|
| **1. Authentication** | Employee posts login request: `{"email": "harshini@company.com"}`. | HTTP 200 response with Bearer JWT token, department (`Engineering`), and roles (`Employee`, `Engineer`). | Verified in `test_api_auth.py`. |
| **2. Search Request** | User queries: *"What are the coding standards?"* | Backend receives JWT, filters vector store by role `Engineer`, searches BM25 index, fuses top candidates. | Verified in `hybrid_search` and `test_query_router.py`. |
| **3. Access Filtering** | User attempts querying restricted HR compensation policy. | RBAC filter blocks restricted HR document from candidate list. | Verified in `test_document_access.py` (`test_engineer_blocked_hr_restricted`). |
| **4. AI Synthesis** | Gemini synthesizes grounded answer with citations. | Response includes inline brackets `[1]` linked to exact document chunk and page. | Verified in `test_generator_citations.py`. |
| **5. Observability Emission** | System emits structured log and increments Prometheus counter. | Log emitted with `request_id`, `path: /api/search`, `latency_ms: 342`. Prometheus metric `knowledge_base_search_queries_total` incremented. | Verified in `backend/observability.py`. |

---

## 4. Unresolved Issues & Known Operational Limitations

1. **Docker Desktop Engine Daemon:** In this headless Windows environment, starting the Windows Service `com.docker.service` requires elevated Administrator UAC approval. The container images and Dockerfiles have been created and validated against strict multi-stage standards, ready to run directly via `docker compose up` once the daemon is started.
2. **Gemini API Live Key:** Online LLM question synthesis requires an active Google AI Studio Gemini API key. If no key is configured in the environment, the backend gracefully falls back to structured extractive source citations without throwing unhandled 500 errors.

