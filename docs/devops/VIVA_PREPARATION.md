# Viva Voce Preparation Guide: Knowledge Base DevOps Project

## 1. Two-Minute Project Pitch (Elevator Pitch)

> "The **Knowledge Base** (EKIP) is an enterprise Retrieval-Augmented Generation (RAG) platform with strict Role-Based Access Control (RBAC). It enables employees in HR, Engineering, and Sales to search corporate policies and incident reports and receive accurate, AI-generated answers with inline citations grounded in source documents and PDF page numbers.
>
> My objective for this Scaler Advanced DevOps capstone was to transform this existing monolithic, locally-run application into an enterprise-ready, containerized, and observable Kubernetes workload.
>
> To achieve this without altering the underlying search and RAG business logic:
> 1. I preserved the original project baseline at commit `93dcb834893ab486bdae244ea2a6a3e88a7b30ba` on the `main` branch.
> 2. I decoupled the application into independent multi-stage, non-root containers for the React/NGINX frontend and the FastAPI backend.
> 3. I authored production Kubernetes manifests for stateless Deployments with rolling updates, persistent storage for PostgreSQL and Qdrant via PersistentVolumeClaims, and least-privilege NetworkPolicies.
> 4. I implemented a robust observability stack with tri-partite Kubernetes probes (`/live`, `/ready`, `/startup`), structured JSON access logs with request correlation IDs, and Prometheus metrics visualized in a custom Grafana dashboard.
> 5. Finally, I built an automated GitHub Actions CI/CD pipeline featuring automated linting, test suites, and Trivy security scans, delivering everything in a single, transparent pull request."

---

## 2. Architecture & Request Walkthrough

### From Git Commit to Production Deployment
1. **Developer Work:** Changes are committed to a feature branch and pushed to GitHub.
2. **CI Pipeline Gate:** GitHub Actions triggers on PR/push:
   - Flake8 and ESLint validate syntax and code formatting.
   - Pytest executes backend unit tests and Vitest executes frontend tests.
   - Trivy scans dependencies and filesystems for CVEs and secret leaks.
   - Multi-stage Dockerfiles build container images tagged with the Git commit SHA (`kb-backend:v1.0.0-${SHA::7}`).
   - `kubectl kustomize k8s/` dry-run validates Kubernetes resource syntax.
3. **Deployment Delivery:** Container images are published to the container registry and deployed to Kubernetes via `kubectl apply -k k8s/`.

### From User Request to Database & AI Synthesis
1. An engineer enters `What is the incident response procedure?` in the React frontend.
2. The browser sends a `POST /api/search` with a Bearer JWT to the NGINX frontend service on port 80.
3. NGINX reverse-proxies the request internally to `http://backend-svc:8000/api/search`.
4. `ObservabilityMiddleware` intercepts the request, assigns a unique `X-Request-ID` correlation header, and starts latency timing.
5. `auth_router` validates the JWT token against `JWT_SECRET`, extracting user roles (`Engineer`) and department.
6. The hybrid retrieval engine initiates parallel searches:
   - **Vector Branch:** Calls Qdrant (`qdrant-svc:6333`) using payload filter `access_roles IN ['Engineer', 'Employee']`.
   - **Keyword Branch:** Whoosh searches BM25 inverted index in `indexdir/` and filters results against RBAC rules.
7. Reciprocal Rank Fusion (RRF) merges candidate lists; Cross-Encoder scores and reranks the top 8 chunks.
8. The backend prompts Google Gemini 2.5 Flash with the retrieved excerpts.
9. Gemini synthesizes an answer with citation tags `[1]`, which the backend maps to document metadata and exact PDF page numbers.
10. The backend logs the query in PostgreSQL `access_audit_log` via SQLAlchemy, emits a structured JSON log to stdout, increments Prometheus counters, and returns the response to the user.

---

## 3. Deep-Dive Viva Questions & Answers

### Q1: Why did you choose Kubernetes Deployments with PVCs instead of StatefulSets for PostgreSQL and Qdrant?
**Answer:**
"For single-node datastore instances in a local or single-cluster environment, StatefulSets introduce unnecessary complexity around ordinal pod indexing and headless services without providing distributed consensus. A Kubernetes Deployment with `replicas: 1`, `strategy: Recreate`, and a PersistentVolumeClaim (`postgres-pvc`, `qdrant-pvc`) guarantees data persistence across pod restarts while keeping the operational model simple and reliable. If we scale to a distributed PostgreSQL cluster with streaming replication or a multi-node Qdrant Raft cluster, we would transition to StatefulSets."

---

### Q2: Why did you implement three separate health endpoints (`/live`, `/ready`, `/startup`)?
**Answer:**
"FastAPI backend containers load heavy machine learning weights (`sentence-transformers/all-MiniLM-L6-v2` and cross-encoders) during initialization, which can take 10 to 25 seconds on cold starts.
- A **Startup Probe** (`/api/health/startup`) gives the pod up to 60 seconds to initialize without premature termination.
- A **Liveness Probe** (`/api/health/live`) checks that the Python process and event loop are responsive.
- A **Readiness Probe** (`/api/health/ready`) verifies live connectivity to PostgreSQL (`SELECT 1`) and Qdrant. If the database experiences a transient blip, the readiness probe fails and Kubernetes immediately removes the pod from the load balancer pool without triggering an aggressive restart loop."

---

### Q3: How do you handle secrets securely in Git and Kubernetes?
**Answer:**
"I adhere to strict credential hygiene:
1. No production passwords, JWT secrets, or Gemini API keys are committed to Git. All `.env` files are excluded via `.gitignore` and `.dockerignore`.
2. A `.env.example` file and a `k8s/secret.template.yaml` provide clear placeholder templates.
3. In Kubernetes, sensitive variables are decoupled into a Kubernetes Secret (`kb-secret`), while non-sensitive settings (hostnames, ports, log levels) reside in a ConfigMap (`kb-config`).
4. In production environments, I would integrate the Kubernetes External Secrets Operator (ESO) backed by HashiCorp Vault or AWS Secrets Manager to dynamically rotate credentials."

---

### Q4: How does a zero-downtime rolling update work, and how do you roll back a bad release?
**Answer:**
"In [`k8s/backend-deployment.yaml`](../../k8s/backend-deployment.yaml), I configured `strategy: RollingUpdate` with `maxSurge: 1` and `maxUnavailable: 0`.
When an updated image is applied:
1. Kubernetes spins up a new pod with the new image revision while keeping both old pods active.
2. The new pod is evaluated by the startup and readiness probes.
3. Once the new pod reports healthy, traffic is routed to it and one old pod is gracefully terminated.
4. If the new revision exhibits errors or latency spikes, rollback is executed instantaneously with:
   `kubectl rollout undo deployment/backend -n knowledge-base`.
   Kubernetes reverts the ReplicaSet to the prior known-healthy revision. Because the datastores reside on decoupled PVCs, data remains completely intact."

---

### Q5: How would the architecture scale if traffic increased by 100x?
**Answer:**
"To handle a 100x traffic increase:
1. **Stateless Tier Autoscaling:** Implement Horizontal Pod Autoscalers (HPA) for the frontend and backend deployments, scaling horizontally based on CPU utilization and custom Prometheus metrics (request rate).
2. **Model Caching & Asynchronous Ingestion:** Separate the CPU-heavy neural embedding inference from the synchronous web API into an asynchronous worker pool (Celery/RabbitMQ or Redis queues).
3. **Database Read Replicas:** Transition PostgreSQL to a primary-replica cluster using PgBouncer for connection pooling, routing search audit writes to the primary and user read queries to read replicas.
4. **Distributed Vector Cluster:** Deploy Qdrant in distributed cluster mode with multiple shards and replication factors across Kubernetes nodes.
5. **Edge Caching & CDN:** Cache compiled static frontend assets on Cloudflare or Fastly CDN."

---

### Q6: What happens if the PostgreSQL database goes down while the application is running?
**Answer:**
"1. The backend's readiness probe (`/api/health/ready`) immediately detects that `SELECT 1` has failed and returns HTTP 503 `status: not_ready`.
2. Kubernetes pulls that backend pod out of the `backend-svc` endpoint pool so no new end-user traffic is sent to it.
3. Crucially, the liveness probe (`/api/health/live`) does NOT fail, preventing Kubernetes from aggressively restarting the healthy API process in a futile reboot loop while waiting for the database to recover.
4. Once PostgreSQL recovers, the readiness probe passes and the backend seamlessly resumes serving requests."

---

### Q7: What are the project's honest limitations?
**Answer:**
"1. **Gemini API Egress:** The AI synthesis feature depends on outbound internet access to Google AI Studio. In an air-gapped corporate network, this would require hosting a local open-source LLM like Llama 3 via Ollama or vLLM.
2. **Local Machine Docker Daemon:** In this headless Windows environment, starting Docker Desktop requires elevated administrative privileges, but the containerization, Kubernetes manifests, and CI/CD pipelines have been fully authored and verified via unit tests and dry-run syntax checks."

