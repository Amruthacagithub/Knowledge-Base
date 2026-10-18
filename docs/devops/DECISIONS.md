# Architectural Decision Records (ADRs): Knowledge Base Platform

This document captures the key architectural and operational decisions made while enhancing the Knowledge Base application for production-grade DevOps deployment.

---

## ADR-001: Multi-Container Decoupled Architecture vs Monolithic Single Container

### Status: Accepted
### Context:
In the original baseline, the frontend had no Dockerfile (it was run via `npm run dev` or deployed to Vercel), while the backend Dockerfile ran as a standalone container on Google Cloud Run. To deploy the entire system repeatably on Kubernetes or local Docker, we had to choose between:
1. Bundling the Node/React frontend and FastAPI backend into a single container running a process supervisor (e.g. supervisord).
2. Creating independent, decoupled container images for Frontend (served via optimized NGINX Alpine) and Backend (FastAPI).

### Decision:
We adopted option 2: independent container images.
- The **Frontend** is packaged into a multi-stage Alpine NGINX container that compiles static assets and reverse-proxies `/api/` traffic to the backend service.
- The **Backend** is packaged into a Python 3.11-slim container focused exclusively on API routing and RAG inference.

### Consequences:
- **Pros:** Independent scaling (frontend can scale with UI traffic without multiplying heavy ML backend instances); smaller attack surface; independent build caching; faster rebuilds when only UI or API changes.
- **Cons:** Requires managing two container images and internal service routing.
- **Mitigation:** Unified `docker-compose.yml` and Kubernetes manifests orchestrate both containers cleanly.

---

## ADR-002: Modular Kubernetes Manifests with Kustomization vs Helm Charts

### Status: Accepted
### Context:
The rubric permits either Helm or clean, reusable Kubernetes manifests. For local environments (Minikube, kind, Docker Desktop) and student assessment, Helm introduces additional template indirection (`values.yaml`, Go templates) and external dependency overhead.

### Decision:
We implemented clean, modular Kubernetes manifests orchestrated via native `kustomization.yaml` (`kubectl apply -k k8s/`).

### Consequences:
- **Pros:** 100% native Kubernetes toolchain (`kubectl`) without requiring Helm binary installation; straightforward readability during viva assessment; zero template rendering bugs.
- **Cons:** Less dynamic for parameterized multi-environment deployments.
- **When Helm would be better:** In multi-tenant enterprise environments where multiple ephemeral staging environments are provisioned across dozens of clusters with dynamic domain names.

---

## ADR-003: Kubernetes Deployments with PersistentVolumeClaims vs StatefulSets for Datastores

### Status: Accepted
### Context:
The application relies on PostgreSQL and Qdrant. A common mistake is introducing StatefulSets unnecessarily for single-replica local database workloads, which adds ordinal pod management complexity without providing distributed consensus.

### Decision:
We use standard Kubernetes Deployments with `replicas: 1` backed by PersistentVolumeClaims (`postgres-pvc` and `qdrant-pvc`) using `ReadWriteOnce` access mode.

### Consequences:
- **Pros:** Simpler operational model; automatic pod recreation on node failure; persistent disk storage retains all users, roles, embeddings, and audit logs across pod restarts.
- **Cons:** Single-replica database does not provide multi-master replication.
- **When StatefulSets would be better:** If deploying a clustered PostgreSQL cluster with Patroni / Stolon or a multi-node distributed Qdrant cluster with Raft consensus.

---

## ADR-004: Tri-Partite Health Probing Architecture (`/live`, `/ready`, `/startup`)

### Status: Accepted
### Context:
The backend loads sentence-transformer neural embedding models and cross-encoders into memory. In low-resource environments (or initial cold starts), this model loading process takes 10–25 seconds.
Using a single naive liveness probe with a short timeout causes Kubernetes to prematurely kill the pod while it is still initializing its ML weights, leading to CrashLoopBackOff loops.

### Decision:
We implemented three specialized endpoints:
1. `/api/health/startup`: Gives the container up to 60 seconds (`failureThreshold: 12`, `periodSeconds: 5`) to download/load ML models.
2. `/api/health/live`: Fast process liveness check (fails only if the Python event loop is deadlocked).
3. `/api/health/ready`: Deep dependency check (queries `SELECT 1` on PostgreSQL and collection status on Qdrant). If the database is temporarily unreachable, the pod is removed from the Service endpoint pool without being restarted.

### Consequences:
- **Pros:** Prevents false-positive container restarts during ML model loading; ensures zero downtime during rolling upgrades.
- **Cons:** Requires explicit probe configuration in Kubernetes Deployment specs.

---

## ADR-005: Non-Root Unprivileged Container Security Baseline

### Status: Accepted
### Context:
Containers running as root (`UID 0`) violate enterprise security baselines and principle of least privilege, enabling container-escape vulnerabilities to compromise the host node.

### Decision:
- **Backend:** Creates a non-root system user `appuser` (UID 10001) in the Dockerfile; files are owned by `appuser`; container runs under `USER 10001`.
- **Frontend:** Built on `nginxinc/nginx-unprivileged:alpine`, listening on unprivileged port 80/8080 without root rights.
- **Kubernetes SecurityContext:** Enforces `runAsNonRoot: true`, `allowPrivilegeEscalation: false`, and drops all Linux capabilities (`capabilities: drop: ["ALL"]`).

### Consequences:
- **Pros:** Defense-in-depth against container escapes; satisfies CIS Kubernetes benchmark and Trivy compliance checks.
- **Cons:** Container cannot bind to privileged ports (< 1024) or perform root package installations at runtime.

---

## ADR-006: Prometheus Pull-Based Metrics Instrumentation

### Status: Accepted
### Context:
To provide actionable operational signals for SRE monitoring and viva demonstrations, the application needed request count, latency distribution, and error rate tracking.

### Decision:
We instrumented the FastAPI backend with standard Prometheus metrics exposed at `/metrics`:
- `http_requests_total`: Counter by method, endpoint, and status code.
- `http_request_duration_seconds`: Histogram tracking request latency distribution.
- `search_queries_total`: Business metric tracking search queries by query type.
- `rag_generation_latency_seconds`: Latency of Gemini LLM calls.

### Consequences:
- **Pros:** Industry-standard Prometheus format; low overhead; compatible with Prometheus, OpenTelemetry Collector, and Grafana.
- **Cons:** Adds `prometheus-client` dependency.

---

## ADR-007: GitHub Actions CI with Trivy Vulnerability Scanning

### Status: Accepted
### Context:
The baseline lacked continuous integration, relying on manual Cloud Build invocations. We needed an automated pipeline triggered on pull requests and branch pushes.

### Decision:
We implemented a multi-stage GitHub Actions workflow (`.github/workflows/ci.yml`) including:
1. Python Flake8 & Node ESLint linting.
2. Backend Pytest & Frontend Vitest test execution.
3. Trivy vulnerability scanning for repository dependencies and Docker images.
4. Multi-stage Docker image builds.
5. Kubernetes manifest dry-run validation.

### Consequences:
- **Pros:** Automated quality gate on every PR; prevents vulnerable dependencies from entering the main branch; transparent review for evaluators.
- **Cons:** Requires GitHub Actions runner minutes.

