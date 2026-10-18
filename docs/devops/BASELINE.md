# Knowledge Base — DevOps Baseline Record

## 1. Project Identification

| Parameter | Details |
|---|---|
| **Project Name** | Knowledge Base (Internal Knowledge Assistant / EKIP) |
| **Student / Author** | Amrutha |
| **Student Identifier** | 23BCS10158 (Amrutha.23BCS10158@ms.sst.scaler.com) |
| **Repository URL** | `https://github.com/Amruthacagithub/Knowledge-Base.git` |
| **Baseline Branch** | `main` |
| **Baseline Full Commit Hash** | `93dcb834893ab486bdae244ea2a6a3e88a7b30ba` |
| **Baseline Commit Date** | Fri Aug 28 15:23:07 2026 +0530 |
| **Baseline Commit Message** | `Initial commit` |
| **Target Submission Branch** | `devops-improvements` |
| **Submission Deadline** | 18 October 2026, 11:59 PM |

---

## 2. Original Project Description

The Knowledge Base is an enterprise Retrieval-Augmented Generation (RAG) system with Role-Based Access Control (RBAC). It enables employees in HR, Engineering, and Sales to securely query enterprise documents (Markdown policies and PDF reports) and receive accurate, cited AI answers generated via Google Gemini 2.5 Flash, strictly enforcing organizational privacy and department authorization boundaries.

### Key Functional Capabilities of Baseline:
1. **Multi-Role Authentication & Access Control:**
   - Pre-configured demo users (`amrutha` [HR], `harshini` [Engineer], `tanvi` [Sales], `bhaskar` [Admin], `arijith` [Employee]).
   - Document classification into `public` and `restricted`.
2. **Hybrid Retrieval Pipeline:**
   - Semantic vector search via Qdrant (384-dimensional dense vectors using `sentence-transformers/all-MiniLM-L6-v2`).
   - Keyword search via Whoosh BM25 index.
   - Reciprocal Rank Fusion (RRF) and Cross-Encoder reranking (`cross-encoder/ms-marco-MiniLM-L-6-v2`).
3. **Cited AI Synthesis:**
   - Answers generated with bracketed citations (`[1]`, `[2]`), linked to source documents and exact PDF page numbers.
4. **Interactive Web Interface:**
   - React 19 + Vite three-pane application with real-time markdown rendering, citation preview drawer, document viewer modal with text highlighter, and admin upload modal.

---

## 3. Existing DevOps Capabilities in Baseline

Before the DevOps enhancement engagement, the repository included the following initial artifacts:

| Area | Baseline State | Evaluation / Gaps |
|---|---|---|
| **Containerization** | Single `Dockerfile` in `KB-main/` targeting Google Cloud Run; no frontend container. | Single-stage, runs as `root`, hardcoded port 8080, copies whole repo, downloads ML models on cold start without caching. |
| **Local Orchestration** | `docker-compose.yml` defining PostgreSQL 16 and Qdrant containers. | Backend and Frontend were not containerized in Docker Compose; only supporting datastores were defined. |
| **Cloud Deployment** | Manual instructions in `docs/DEPLOY.md` (Vercel + Cloud Run + Supabase + Qdrant Cloud) and `cloudbuild.yaml`. | Relied entirely on external SaaS platforms and manual CLI triggers (`gcloud builds submit`); no automated GitOps or infrastructure manifests. |
| **Kubernetes** | Completely absent. | No Deployments, Services, ConfigMaps, Secrets, Ingress, probes, or resource controls. |
| **CI/CD** | Completely absent. | No `.github/workflows` directory; no automated test or lint triggers on push or PR. |
| **Observability** | Minimal `/api/health` checking Postgres and Qdrant connectivity. | No Prometheus metrics, no structured JSON logging, no request correlation IDs, no Grafana dashboards. |
| **Security Controls** | `.env.example` provided; `.env` gitignored. | Container runs as root; no automated vulnerability scanning, no SAST, no container image scans, no Kubernetes NetworkPolicies. |
| **Release Management** | Mutable `:latest` tags; manual branch tracking (`v1` vs `v2`). | No semantic versioning, no automated rollback mechanism, no build metadata or commit SHA exposure. |

---

## 4. Instructions for Checking Out and Running the Baseline

To inspect or execute the baseline state exactly as it existed before any DevOps enhancements:

### Step 1: Clone and Checkout Baseline Commit
```bash
git clone https://github.com/Amruthacagithub/Knowledge-Base.git
cd Knowledge-Base
git checkout 93dcb834893ab486bdae244ea2a6a3e88a7b30ba
```

### Step 2: Set Up Local Environment
```powershell
cd KB-main

# Create and activate Python virtual environment
python -m venv venv
.\venv\Scripts\activate
pip install -r requirements.txt

# Configure environment variables
copy .env.example .env
# Edit .env and supply a GEMINI_API_KEY if testing AI generation

# Start datastores
docker compose up -d

# Initialize database schema and seed users
python scripts/init_db.py

# Ingest initial document corpus
python scripts/build_pdf_corpus.py
python scripts/ingest.py
```

### Step 3: Run Baseline Application
```powershell
# In terminal 1 (Backend):
python -m uvicorn backend.main:app --host 0.0.0.0 --port 8000 --reload

# In terminal 2 (Frontend):
cd frontend
npm install
npm run dev
```

### Step 4: Run Baseline Unit Tests
```powershell
# Backend non-integration tests:
pytest tests/ -m "not integration" -q

# Frontend tests:
cd frontend
npm run test
```

---

## 5. Verification Guarantee

- The commit `93dcb834893ab486bdae244ea2a6a3e88a7b30ba` remains untouched on the `main` branch.
- All new DevOps improvements, container configurations, Kubernetes manifests, CI/CD pipelines, and documentation are authored on the `devops-improvements` branch and submitted through a single pull request for clear, transparent review against this baseline.

