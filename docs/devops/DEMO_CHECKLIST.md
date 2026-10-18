# Live Demonstration Checklist: Knowledge Base Platform

This checklist guides the live demonstration of the Knowledge Base DevOps project during viva voce assessment.

---

## 1. Pre-Demo Setup & Preparation

- [ ] **Terminal Setup:** Open two terminal panes (Terminal 1 for executing commands, Terminal 2 for monitoring logs/pods).
- [ ] **Browser Tabs Ready:**
  1. Frontend UI: `http://localhost:30080` (or `http://localhost:3000`)
  2. Backend Health: `http://localhost:8000/api/health`
  3. Version Metadata: `http://localhost:8000/api/version`
  4. Prometheus Metrics: `http://localhost:8000/metrics`
  5. GitHub Pull Request: Pull request view comparing `devops-improvements` against `main`.

---

## 2. Step-by-Step Demonstration Script

### Step 1: Baseline Preservation & Single PR Evidence (2 mins)
- **Show Baseline Commit:**
  ```bash
  git log -n 1 main
  ```
  *Point out:* Baseline commit `93dcb834893ab486bdae244ea2a6a3e88a7b30ba` remains untouched.
- **Show Current Working Branch:**
  ```bash
  git status
  ```
  *Point out:* All DevOps enhancements reside cleanly on `devops-improvements`.
- **Show Git Diff Summary:**
  ```bash
  git diff --stat main..devops-improvements
  ```
  *Point out:* Only DevOps infrastructure, tests, observability, and docs were added; original application logic is preserved.

---

### Step 2: Kubernetes Manifests & Kustomize Rendering (2 mins)
- **Render Manifests:**
  ```bash
  kubectl kustomize k8s/
  ```
  *Point out:*
  1. Multi-tier isolation (`namespace: knowledge-base`).
  2. Non-root security contexts (`runAsUser: 10001`).
  3. Tri-partite probes (`/api/health/startup`, `/api/health/live`, `/api/health/ready`).
  4. Persistent storage via PVCs (`postgres-pvc`, `qdrant-pvc`).
  5. NetworkPolicies for datastore isolation.

---

### Step 3: Application Deployment & Pod Health (2 mins)
- **Inspect Live Workloads:**
  ```bash
  kubectl get pods,services,pvc -n knowledge-base -o wide
  ```
  *Point out:*
  - 2 Backend replicas running and ready (`2/2`).
  - 2 Frontend replicas running and ready (`2/2`).
  - PVCs bound and persistent (`Bound`).

---

### Step 4: End-to-End Application Workflow & RBAC Demo (3 mins)
1. **Login:** Log in as Harshini (`harshini@company.com` [Engineer]).
2. **Search Query:** Search for *"coding standards"*. Show retrieved citations with document metadata.
3. **RBAC Isolation:** Search for restricted HR salary policies. Show that the document is securely hidden and blocked by the RBAC filter.
4. **Admin Panel:** Log in as Bhaskar (`bhaskar@company.com` [Admin]) to show document upload capability.

---

### Step 5: Observability, Metrics & Structured Logging (2 mins)
- **Inspect Structured Logs:**
  ```bash
  kubectl logs -l app=backend -n knowledge-base --tail=20
  ```
  *Point out:* JSON log structure, correlation ID `X-Request-ID`, endpoint, and latency.
- **Inspect Prometheus Metrics:**
  ```bash
  curl -s http://localhost:8000/metrics | grep "knowledge_base"
  ```
  *Point out:* `knowledge_base_http_requests_total`, `knowledge_base_http_request_duration_seconds`, and `knowledge_base_search_queries_total`.

---

### Step 6: Zero-Downtime Rollout & Instant Rollback Demo (2 mins)
- **Simulate Rolling Update:**
  ```bash
  kubectl set image deployment/backend backend=kb-backend:v1.1.0 -n knowledge-base
  kubectl rollout status deployment/backend -n knowledge-base
  ```
  *Point out:* Kubernetes updates one pod at a time; zero search downtime.
- **Execute Rollback:**
  ```bash
  kubectl rollout undo deployment/backend -n knowledge-base
  kubectl rollout status deployment/backend -n knowledge-base
  ```
  *Point out:* Rollback completes in seconds; history preserves revision logs.

---

### Step 7: Security & Non-Root Verification (1 min)
- **Verify Non-Root UID:**
  ```bash
  kubectl exec -it deployment/backend -n knowledge-base -- id
  ```
  *Expected Output:* `uid=10001(appuser) gid=10001(appgroup) groups=10001(appgroup)`
  *Point out:* Container executes with zero root permissions, satisfying CIS Kubernetes benchmark standards.

---

## 3. Demo Contingency & Fallback Strategy

- If the local Kubernetes cluster has an issue, execute:
  `docker compose up -d` to demonstrate the exact same multi-tier containers running in Docker Compose.
- If the Gemini API hits a rate limit, the backend automatically transitions to fallback citation extraction mode without crashing.
- Pre-recorded CLI execution evidence is documented in [`docs/devops/TEST_RESULTS.md`](./TEST_RESULTS.md).

