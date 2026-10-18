# DevOps Deployment & Operations Runbook: Knowledge Base Platform

## 1. Overview & Operational Principles

This runbook provides tested, step-by-step operational instructions for building, deploying, updating, troubleshooting, and rolling back the Knowledge Base platform across local developer workstations and Kubernetes clusters.

### Core Operational Principles:
- **Immutable Artifacts:** Every build produces immutable container image tags (`kb-backend:v1.0.0-<SHA>`, `kb-frontend:v1.0.0-<SHA>`). Never deploy mutable `:latest` in production.
- **Zero-Downtime Rollouts:** Stateless API and UI tiers utilize Kubernetes rolling updates with `maxSurge: 1` and `maxUnavailable: 0`.
- **Decoupled State:** Persistent storage is decoupled into dedicated PersistentVolumeClaims (`postgres-pvc`, `qdrant-pvc`).
- **Tri-Partite Health Gating:** Readiness probes protect the traffic pool; unready pods never receive search queries.

---

## 2. Prerequisites & Tooling Requirements

Ensure the following tools are installed on the deployment machine:

| Tool | Minimum Version | Verification Command |
|---|---|---|
| **Python** | 3.10+ (tested on 3.11 / 3.13) | `python --version` |
| **Node.js & npm** | Node 18+ / npm 9+ | `node --version; npm --version` |
| **Docker Engine & CLI** | 24.0+ (tested on 28.3) | `docker --version` |
| **kubectl** | 1.28+ (tested on 1.32) | `kubectl version --client` |
| **Kubernetes Cluster** | Minikube, kind, or Docker Desktop K8s | `kubectl cluster-info` |

---

## 3. Deployment Method A: Local 4-Tier Docker Compose

Use this workflow for rapid local developer inner-loop testing.

### Step 1: Clone Repository and Enter Workspace
```bash
git clone https://github.com/Amruthacagithub/Knowledge-Base.git
cd Knowledge-Base
```

### Step 2: Build & Start Services
```powershell
# Using PowerShell automation script:
.\run-devops.ps1 -Target up

# Or using Docker Compose directly:
docker compose up -d --build
```

### Step 3: Verify Container Health
```powershell
docker compose ps
```
*Expected Output:*
- `kb-postgres`: Up (healthy) on `0.0.0.0:5432`
- `kb-qdrant`: Up (healthy) on `0.0.0.0:6333`
- `kb-backend`: Up (healthy) on `0.0.0.0:8000`
- `kb-frontend`: Up (healthy) on `0.0.0.0:80` and `0.0.0.0:3000`

### Step 4: Access Application
- **Frontend UI:** Open [http://localhost](http://localhost) or [http://localhost:3000](http://localhost:3000)
- **Backend API Docs:** Open [http://localhost:8000/docs](http://localhost:8000/docs)
- **Prometheus Metrics:** Open [http://localhost:8000/metrics](http://localhost:8000/metrics)
- **Health Check:** Open [http://localhost:8000/api/health](http://localhost:8000/api/health)

---

## 4. Deployment Method B: Native Kubernetes Deployment

Use this workflow for local Kubernetes (Minikube / kind / Docker Desktop) and production clusters.

### Step 1: Build & Load Local Container Images
When running on local Kubernetes clusters (Minikube or kind), load the built images into the cluster node:

```powershell
# Build container images
docker build -f docker/Dockerfile.backend -t kb-backend:v1.0.0 .
docker build -f docker/Dockerfile.frontend -t kb-frontend:v1.0.0 .

# If using Minikube:
# minikube image load kb-backend:v1.0.0
# minikube image load kb-frontend:v1.0.0

# If using kind:
# kind load docker-image kb-backend:v1.0.0
# kind load docker-image kb-frontend:v1.0.0
```

### Step 2: Configure Secrets
Create the secret manifest from template or inject via CLI:
```powershell
kubectl apply -f k8s/namespace.yaml

# Generate secret dynamically with safe local credentials:
kubectl create secret generic kb-secret -n knowledge-base \
  --from-literal=POSTGRES_PASSWORD=ekip_dev_2026 \
  --from-literal=JWT_SECRET=ekip-local-secret-change-in-prod \
  --from-literal=GEMINI_API_KEY="" \
  --dry-run=client -o yaml | kubectl apply -f -
```

### Step 3: Deploy All Kubernetes Resources
```powershell
# Using Kustomize (or .\run-devops.ps1 -Target k8s-up):
kubectl apply -k k8s/
```

### Step 4: Monitor Rollout Progress
```powershell
kubectl rollout status deployment/postgres -n knowledge-base --timeout=120s
kubectl rollout status deployment/qdrant -n knowledge-base --timeout=120s
kubectl rollout status deployment/backend -n knowledge-base --timeout=180s
kubectl rollout status deployment/frontend -n knowledge-base --timeout=120s
```

### Step 5: Verify Running Workloads & Persistent Storage
```powershell
kubectl get pods,services,pvc -n knowledge-base -o wide
```
*Expected Output:*
```text
NAME                            READY   STATUS    RESTARTS   AGE
pod/backend-67df98b84d-x7f2a    1/1     Running   0          45s
pod/backend-67df98b84d-k9l1b    1/1     Running   0          45s
pod/frontend-5cb8d799f8-b2m4c   1/1     Running   0          45s
pod/frontend-5cb8d799f8-p4q8w   1/1     Running   0          45s
pod/postgres-7468b8cf4d-v5s8x   1/1     Running   0          45s
pod/qdrant-6cf7d477cb-h7t3q     1/1     Running   0          45s

NAME                   TYPE        CLUSTER-IP       PORT(S)          AGE
service/backend-svc    ClusterIP   10.96.142.12     8000/TCP         45s
service/frontend-svc   NodePort    10.96.201.88     80:30080/TCP     45s
service/postgres-svc   ClusterIP   10.96.88.54      5432/TCP         45s
service/qdrant-svc     ClusterIP   10.96.110.22     6333/TCP         45s
```

### Step 6: Access the Application on Kubernetes
- **NodePort Access:** If using Docker Desktop / Minikube, browse to `http://localhost:30080`
- **Port-Forwarding (Alternative):**
  ```powershell
  kubectl port-forward svc/frontend-svc 8080:80 -n knowledge-base
  # Browse to http://localhost:8080
  ```

---

## 5. Safe Rollout & Zero-Downtime Release Procedure

When deploying an upgraded image version (e.g. `kb-backend:v1.1.0`):

1. **Build and Tag New Artifact:**
   ```bash
   docker build -f docker/Dockerfile.backend -t kb-backend:v1.1.0 .
   ```
2. **Apply Image Update to Deployment:**
   ```bash
   kubectl set image deployment/backend backend=kb-backend:v1.1.0 -n knowledge-base --record
   ```
3. **Observe Kubernetes Rolling Update Mechanics:**
   - Kubernetes schedules Pod 1 of revision 2.
   - Traffic continues flowing to Pods 1 & 2 of revision 1.
   - Pod 1 (v1.1.0) executes `startupProbe` and `readinessProbe`.
   - Once healthy, Kubernetes adds Pod 1 (v1.1.0) to `backend-svc` and terminates Pod 1 (v1.0.0).
   - Process repeats for Pod 2. Zero search downtime is incurred.
4. **Inspect Rollout History:**
   ```bash
   kubectl rollout history deployment/backend -n knowledge-base
   ```

---

## 6. Rollback Runbook (Disaster Recovery)

If a new release causes latency spikes, unhandled exceptions, or regression bugs:

### Scenario 1: Immediate Automated Rollback via Kubernetes
```powershell
# Check current rollout revision
kubectl rollout history deployment/backend -n knowledge-base

# Roll back to the immediately preceding stable revision
kubectl rollout undo deployment/backend -n knowledge-base

# Or roll back to a specific revision number (e.g., Revision 1)
kubectl rollout undo deployment/backend -n knowledge-base --to-revision=1

# Confirm rollout completion
kubectl rollout status deployment/backend -n knowledge-base
```

### Scenario 2: Database Schema & Migration Rollback Considerations
- **Non-Destructive Migrations:** Always ensure database schema changes are backward-compatible (expand-and-contract pattern: add columns with defaults; do not drop columns in the same release as code changes).
- **Persistent Storage Safety:** Rolling back the backend deployment does NOT delete or reset the PostgreSQL or Qdrant PersistentVolumeClaims (`postgres-pvc`, `qdrant-pvc`). Data remains intact.

### Scenario 3: Correcting Configuration Drift
To verify whether the cluster state matches committed Git manifests:
```powershell
# Diff cluster state against Git repository
kubectl diff -k k8s/

# Re-apply source of truth
kubectl apply -k k8s/
```

---

## 7. Troubleshooting Guide: Common Failure Signatures

| Failure Signature | Probable Root Cause | Investigation Command | Remediation Action |
|---|---|---|---|
| **CrashLoopBackOff on Backend** | Container failed startup or missing environment variable. | `kubectl logs deployment/backend -n knowledge-base --previous` | Check logs for missing Python dependencies or syntax error. |
| **Pod Stuck in Pending** | Insufficient CPU/Memory or PVC cannot bind. | `kubectl describe pod <pod-name> -n knowledge-base` | Inspect cluster resource quotas; check default StorageClass for PVC binding. |
| **503 Service Unavailable on Search** | Datastore readiness probe failing or Postgres offline. | `kubectl get pods -n knowledge-base`<br>`curl http://<svc-ip>:8000/api/health/ready` | Check `postgres` pod status; inspect postgres container logs: `kubectl logs deployment/postgres -n knowledge-base`. |
| **OOMKilled on Backend** | ML inference exceeded 2Gi memory limit during peak query. | `kubectl describe pod <pod-name> -n knowledge-base \| grep -i oom` | Increase `resources.limits.memory` in `k8s/backend-deployment.yaml` from 2Gi to 3Gi. |
| **ImagePullBackOff** | Image name or tag does not exist locally or in registry. | `kubectl describe pod <pod-name> -n knowledge-base` | Run `minikube image load <image>` or verify image tag spelling in deployment YAML. |
