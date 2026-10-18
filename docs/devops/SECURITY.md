# Security Architecture & Hardening Guide: Knowledge Base Platform

## 1. Security Posture & Threat Model

The Knowledge Base platform handles enterprise confidential and restricted documentation (HR policies, executive compensation, engineering incident post-mortems). Security is applied across development, supply chain delivery, and runtime execution using defense-in-depth principles.

---

## 2. Container & Runtime Hardening

### Non-Root Execution
- **Backend:** Executes under non-root system user `appuser` (UID `10001`, GID `10001`). Root execution is explicitly prohibited.
- **Frontend:** Runs unprivileged NGINX (UID `101`) on non-privileged port `80`.
- **Kubernetes Pod Security Standards:**
  Enforces restricted pod security standards in [`k8s/backend-deployment.yaml`](../../k8s/backend-deployment.yaml):
  ```yaml
  securityContext:
    runAsNonRoot: true
    runAsUser: 10001
    runAsGroup: 10001
    fsGroup: 10001
  containers:
    - name: backend
      securityContext:
        allowPrivilegeEscalation: false
        capabilities:
          drop: ["ALL"]
  ```

### Multi-Stage Attack Surface Reduction
- **Build Tools Removed:** Compilers (`gcc`), header files (`libpq-dev`), and package managers are isolated to the build stage and absent from the final production runtime container.
- **Base Images:** Built on minimal official Debian slim (`python:3.11-slim-bookworm`) and Alpine (`node:20-alpine`, `nginx:1.27-alpine`).

---

## 3. Secret Management & Credential Hygiene

### Strict Separation of Configuration & Secrets
1. **Zero Committed Secrets:**
   - No production passwords, JWT signing keys, or Google Gemini API keys are committed to Git.
   - All `.env` files are ignored via `.gitignore` and `.dockerignore`.
2. **Safe Local Developer Workflow:**
   - Template provided at [`.env.example`](../../KB-main/.env.example) with placeholder values.
   - Kubernetes Secret template provided at [`k8s/secret.template.yaml`](../../k8s/secret.template.yaml).
3. **Secret Injection Workflow:**
   Secrets are injected at runtime via Kubernetes Secrets (`kb-secret`) or environment variables, never hardcoded in Docker build arguments or Dockerfile instructions.

### Credential Rotation Runbook
If an API key or password is compromised:
1. Update the secret in the cluster:
   ```bash
   kubectl create secret generic kb-secret -n knowledge-base \
     --from-literal=POSTGRES_PASSWORD=new_strong_password \
     --from-literal=JWT_SECRET=new_jwt_secret \
     --from-literal=GEMINI_API_KEY=new_gemini_key \
     --dry-run=client -o yaml | kubectl apply -f -
   ```
2. Trigger a rolling restart to inject updated secrets into live pods:
   ```bash
   kubectl rollout restart deployment/backend -n knowledge-base
   ```

---

## 4. Application & Authorization Security

### Role-Based Access Control (RBAC)
- Five distinct organizational roles: `Admin`, `HR`, `Engineer`, `Sales`, `Employee`.
- Documents classified as `public` (accessible to all employees) or `restricted` (accessible only to matching department roles or administrators).
- **Dual Verification:** Access permissions are checked during vector search (via Qdrant payload filters), BM25 keyword search (post-retrieval filtering), and full-text document retrieval.

### Input Validation & Upload Controls
- Maximum upload size constrained to 10 MB (`MAX_UPLOAD_BYTES = 10 * 1024 * 1024`).
- Strict file extension allow-list (`.pdf`, `.md`, `.txt`).
- Upload endpoint restricted exclusively to users possessing the `Admin` role.

---

## 5. Network Segmentation & Defense-in-Depth

Kubernetes NetworkPolicies enforce strict tier isolation in [`k8s/network-policy.yaml`](../../k8s/network-policy.yaml):

1. **Datastore Isolation:** PostgreSQL (`:5432`) and Qdrant (`:6333`/`:6334`) deny all ingress traffic by default, accepting connections **only** from backend API pods possessing the label `app: backend`.
2. **Backend Protection:** The backend API accepts incoming traffic **only** from frontend pods (`app: frontend`) and Prometheus monitoring pods.
3. **Frontend Perimeter:** Only the frontend service is exposed externally (via NodePort `:30080` or Ingress), serving compiled assets and proxying requests.

---

## 6. Automated CI/CD Security Scanning

The GitHub Actions pipeline ([`.github/workflows/ci.yml`](../../.github/workflows/ci.yml)) automatically executes:

1. **Static Analysis & Linting:** Detects syntax flaws and security anti-patterns with Flake8 and ESLint.
2. **Trivy Vulnerability Scanner:** Scans the source tree, package manifests, and compiled container images for known Common Vulnerabilities and Exposures (CVEs).
3. **Least-Privilege GitHub Permissions:** Explicitly limits runner tokens to `contents: read` and `security-events: write`.

---

## 7. Known Limitations & Remaining Risks

- **Local Mock Secrets:** In local developer mode without an external secret vault, Kubernetes Secrets use standard base64 encoding. In enterprise production, integration with HashiCorp Vault or AWS Secrets Manager via the Kubernetes External Secrets Operator (ESO) is recommended.
- **External Gemini API Call:** Answer synthesis requires outbound HTTPS traffic to Google AI Studio. If egress network filtering is active in strict air-gapped environments, a self-hosted local LLM (e.g. Ollama / vLLM) would be required.
