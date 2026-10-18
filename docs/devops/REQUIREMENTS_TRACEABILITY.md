# Requirements Traceability Matrix: Scaler Advanced DevOps Submission

This matrix traces every rubric requirement and assignment specification from the Scaler Advanced DevOps Project Rubric to its concrete implementation, associated files, and verification evidence.

---

## 1. Rubric Traceability Table (40 Marks Implementation)

| Rubric Category | Criterion / Requirement | Planned Implementation | Target Files | Verification Evidence & Method | Status |
|---|---|---|---|---|---|
| **1. Architecture & Operation (4 Marks)** | Multi-tier application architecture with clean boundaries, reproducible local environment, and documented request flow. | Multi-tier containerized stack (Frontend, Backend, Postgres, Qdrant, Whoosh). Standardized Makefile and PowerShell scripts for 1-command startup and tear-down. | `docs/devops/ARCHITECTURE.md`<br>`docker-compose.yml`<br>`Makefile`<br>`run-devops.ps1` | Mermaid architecture diagram, Docker Compose service validation, end-to-end user request logs. | Implemented & Documented |
| **2. Kubernetes Workloads (6 Marks)** | Native Kubernetes workloads appropriate to service type; stateless Deployments with replicas, stateful persistent data. | Kubernetes Deployments for Frontend (2 replicas) and Backend (2 replicas). Stateful storage via PersistentVolumeClaims for Postgres and Qdrant. Zero unnecessary StatefulSets. | `k8s/backend-deployment.yaml`<br>`k8s/frontend-deployment.yaml`<br>`k8s/postgres-deployment.yaml`<br>`k8s/qdrant-deployment.yaml`<br>`k8s/pvc.yaml` | `kubectl get pods -n knowledge-base`<br>`kubectl describe deployment backend`<br>Pod restart resilience and PVC persistence test. | Implemented & Documented |
| **3. Deployment Configuration (4 Marks)** | Separation of code and configuration, dynamic environment handling, ConfigMaps and Secrets. | Externalized configuration via ConfigMaps for non-sensitive params (`LOG_LEVEL`, `CORS_ORIGINS`, hosts). Kubernetes Secrets for sensitive credentials (`POSTGRES_PASSWORD`, `GEMINI_API_KEY`, `JWT_SECRET`). `.env.example` reference. | `k8s/configmap.yaml`<br>`k8s/secret.template.yaml`<br>`.env.example`<br>`docs/devops/DEPLOYMENT_RUNBOOK.md` | `kubectl get configmap,secret -n knowledge-base`<br>Verified environment injection in running pods. | Implemented & Documented |
| **4. CI/CD Automation (6 Marks)** | Repeatable CI pipeline for PR and main branch: linting, unit tests, security scans, Docker build, and deployment automation. | GitHub Actions pipeline (`.github/workflows/ci.yml`) with automated stages: Lint, Backend Pytest, Frontend Vitest, Trivy container security scans, multi-stage Docker build, and manifest validation. | `.github/workflows/ci.yml`<br>`.github/workflows/docker-publish.yml` | GitHub Actions workflow execution logs, passing test reports, Trivy vulnerability scan outputs. | Implemented & Documented |
| **5. Release Control & Rollback (4 Marks)** | Versioned releases linked to commit SHA, immutable tags, rollout strategy, documented rollback procedure. | Semantic versioning with commit SHA injection into Docker build (`v1.0.0-${GITHUB_SHA::7}`). Endpoint `/api/version` exposing build metadata. Rolling update strategy with `maxSurge: 1`, `maxUnavailable: 0`. Rollback commands. | `k8s/backend-deployment.yaml`<br>`KB-main/backend/main.py`<br>`docs/devops/DEPLOYMENT_RUNBOOK.md` | `curl /api/version`<br>`kubectl rollout history deployment/backend`<br>`kubectl rollout undo deployment/backend`. | Implemented & Documented |
| **6. Observability & Reliability (6 Marks)** | Health endpoints (liveness, readiness, startup), structured logging, Prometheus metrics, and troubleshooting runbook. | Dedicated `/api/health/live`, `/api/health/ready`, `/api/health/startup` probes. Structured JSON access logging with request latency. Prometheus metrics endpoint at `/metrics`. Pre-built Grafana dashboard JSON. | `KB-main/backend/main.py`<br>`KB-main/backend/observability.py`<br>`monitoring/grafana-dashboard.json`<br>`docs/devops/OBSERVABILITY.md` | `curl /metrics`<br>`curl /api/health/ready`<br>Prometheus scrape logs and sample Grafana panel query. | Implemented & Documented |
| **7. Application Security (4 Marks)** | Non-root containers, no hardcoded secrets, vulnerability scanning, least privilege RBAC, network security. | Dockerfiles use non-root unprivileged users (`appuser` UID 10001, NGINX unprivileged). Automated Trivy image scanner in CI. Kubernetes NetworkPolicy isolating database and vector store to backend namespace traffic. | `docker/Dockerfile.backend`<br>`docker/Dockerfile.frontend`<br>`k8s/network-policy.yaml`<br>`docs/devops/SECURITY.md` | Trivy scan logs, `id` inside container verifying UID != 0, NetworkPolicy verification. | Implemented & Documented |
| **8. Verification & Operational Evidence (10 Marks)** | Full evidence chain: Commit SHA → CI run → Docker image → K8s workload → successful user request → logs/metrics. | Detailed, non-fabricated test logs, command outputs, curl responses, and step-by-step verification traces documented in `TEST_RESULTS.md`. | `docs/devops/TEST_RESULTS.md`<br>`docs/devops/DEMO_CHECKLIST.md` | Verified curl outputs, pytest execution logs, vitest execution logs, docker build logs, kubectl status outputs. | Implemented & Documented |
| **9. Documentation & Reviewability (6 Marks)** | Comprehensive architecture, baseline preservation, runbooks, decision records, and single pull request. | Complete `docs/devops/` suite, single PR branch `devops-improvements`, untouched baseline on `main`, detailed PR description. | `README.md`<br>`docs/devops/*` (11 documents)<br>`docs/devops/DECISIONS.md` | Complete file tree, Git diff against `93dcb834893ab486bdae244ea2a6a3e88a7b30ba`, PR documentation. | Implemented & Documented |

---

## 2. Viva Voce Mapping (30 Marks Viva Preparation)

| Viva Domain | Core Question Addressed | Documentation & Code Reference |
|---|---|---|
| **Architecture Justification** | Why was this specific Kubernetes architecture (Deployments vs StatefulSets, PVCs, Services) chosen for Knowledge Base? | `docs/devops/ARCHITECTURE.md`<br>`docs/devops/DECISIONS.md` (ADR-001, ADR-002) |
| **Configuration & Secrets** | How are runtime settings and sensitive API keys passed to pods without committing secrets to Git? | `docs/devops/DEPLOYMENT_RUNBOOK.md`<br>`docs/devops/SECURITY.md` |
| **Zero-Downtime Rollouts** | How does Kubernetes perform a rolling update when a new image tag is deployed, and how do readiness probes prevent downtime? | `docs/devops/DEPLOYMENT_RUNBOOK.md`<br>`docs/devops/VIVA_PREPARATION.md` |
| **Observability in Action** | If an employee complains search latency has spiked, which logs, metrics, and traces would you inspect? | `docs/devops/OBSERVABILITY.md`<br>`monitoring/grafana-dashboard.json` |
| **Rollback & Disaster Recovery** | If a newly deployed image fails in production, how do you immediately roll back, and what happens to the database? | `docs/devops/DEPLOYMENT_RUNBOOK.md`<br>`docs/devops/VIVA_PREPARATION.md` |
| **Security Boundaries** | What prevents an attacker from escalating privileges from the container to the host node? | `docs/devops/SECURITY.md`<br>`k8s/network-policy.yaml` |

---

## 3. Rubric Verification Checkpoints

- [x] **Baseline Commit Preserved:** Verified commit `93dcb834893ab486bdae244ea2a6a3e88a7b30ba` recorded in `docs/devops/BASELINE.md`.
- [x] **No Unnecessary Scaffolding:** Application code retains all RAG, RBAC, Gemini, and document search logic.
- [x] **Exclusion of Terraform:** Compliant; no Terraform files introduced.
- [x] **Single Pull Request Workflow:** Work managed strictly on `devops-improvements` branching from `main`.
- [x] **Traceability Maintained:** Every file created directly maps to a specific rubric criterion above.

