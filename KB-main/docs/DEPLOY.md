# Deploy Knowledge Base (v2) — step by step

Deploy **v2** (current code) for **$0** on:

| Service | Role |
|---------|------|
| **GitHub** | Source code |
| **Supabase** | Postgres (users, documents metadata) |
| **Qdrant Cloud** | Vector search |
| **Google Cloud Run** | Python API (FastAPI + ML + BM25) |
| **Vercel** | React frontend |
| **Google AI Studio** | Gemini API keys |

**Local development keeps working** — same repo; friends use Docker + `.env` (see [§ Local & friends](#local-development--unchanged)).

**v1 later:** branch `v1` — see [BRANCHING.md](./BRANCHING.md).

---

## Architecture

```text
Browser → Vercel (React)
              ↓  VITE_API_URL
         Cloud Run (FastAPI)
              ↓           ↓
         Supabase     Qdrant Cloud
              ↓
         Gemini API
```

---

## Before you start

- [ ] Google account (Cloud Run + Gemini keys)
- [ ] GitHub repo: `itikelabhaskar/KB` (already connected under `project/`)
- [ ] [Supabase](https://supabase.com) account (free)
- [ ] [Qdrant Cloud](https://cloud.qdrant.io) account (free tier)
- [ ] [Vercel](https://vercel.com) account (hobby)
- [ ] Code works locally (`docker compose up`, ingest, search)

**Expectation (free tier):** API **cold-starts** after ~15+ minutes idle (first search can take **30–60s**). Later searches are much faster until it sleeps again.

### Live v2 (reference — update if you redeploy)

| Service | URL |
|---------|-----|
| **Frontend** | https://novakb.vercel.app |
| **API** | https://kb-api-181317080469.europe-west1.run.app |
| **Health** | `GET …/api/health` → `postgres` + `qdrant` up |
| **API docs** | https://kb-api-181317080469.europe-west1.run.app/docs |

GCP project used: `project-174c756a-f700-4879-ad6` (billing required; free tier + trial credits).

---

## Step 1 — GitHub (save v2, optional v1 branch)

All commands from **`project/`** (the folder that contains `backend/`, `frontend/`, `.git`).

### 1.1 Commit v2 to `main` (when you are ready)

```powershell
cd C:\Users\mylil\Desktop\ONE\BITS_Project\project
git status
git add .
git commit -m "v2: full PoC — UI, PDFs, citations, tests, cloud config"
git push origin main
```

> Do **not** commit `.env` (it is gitignored).

### 1.2 (Optional) Freeze v1 for later

```powershell
git fetch origin
git branch v1 origin/main
git push -u origin v1
```

Details: [BRANCHING.md](./BRANCHING.md).

---

## Step 2 — Supabase (Postgres)

### 2.1 Create project

1. [Supabase Dashboard](https://supabase.com/dashboard) → **New project**.
2. Pick a **region** close to you (e.g. `South Asia` / `US East`).
3. Set a strong **database password** — save it.

### 2.2 Get connection string

1. **Project Settings** → **Database** → **Connection string** → **URI**.
2. Choose **Session mode** or **Transaction pooler** (port `6543` recommended for serverless).
3. Copy the URI; replace `[YOUR-PASSWORD]` with your password.

> **If your password contains `@`, `#`, or `:`** — URL-encode it in the connection string.  
> Example: `Knowledgebase@2026` → `Knowledgebase%402026` (otherwise the host becomes `2026@db....` and connection fails).

Example shape:

```text
postgresql://postgres.xxxxx:YOUR_PASSWORD@aws-0-ap-south-1.pooler.supabase.com:6543/postgres
```

### 2.3 Add to local `.env` (for ingest from your PC)

In `project/.env`:

```env
DATABASE_URL=postgresql://postgres.xxxxx:YOUR_PASSWORD@....pooler.supabase.com:6543/postgres
```

Leave `POSTGRES_HOST` etc. unset when `DATABASE_URL` is set.

### 2.4 Initialize tables & demo users

From `project/` with venv active:

```powershell
.\venv\Scripts\activate
.\venv\Scripts\python.exe scripts\init_db.py
```

You should see users created (bhaskar@company.com, etc.).

---

## Step 3 — Qdrant Cloud (vectors)

### 3.1 Create cluster

1. [Qdrant Cloud](https://cloud.qdrant.io) → **Create cluster** (free tier).
2. Same **region** as Supabase if possible.
3. Create an **API key** (read/write).

### 3.2 Cluster URL

From the cluster page, copy:

- **Cluster URL** (e.g. `https://xxxxxxxx.us-east-1-0.aws.cloud.qdrant.io:6333`)
- **API key**

### 3.3 Add to `.env`

```env
QDRANT_URL=https://YOUR-CLUSTER.cloud.qdrant.io:6333
QDRANT_API_KEY=your-api-key
# QDRANT_HOST and QDRANT_PORT are ignored when QDRANT_URL is set
```

Collection name defaults to `enterprise_docs` (created on first ingest).

---

## Step 4 — Index documents (from your laptop)

Still using **local** code but **cloud** DB + Qdrant.

### 4.1 Gemini keys in `.env`

```env
GEMINI_API_KEY=...
GEMINI_API_KEY_2=...
```

### 4.2 Build PDFs (if not done)

```powershell
.\venv\Scripts\python.exe scripts\build_pdf_corpus.py
```

### 4.3 Ingest into cloud

```powershell
.\venv\Scripts\python.exe scripts\ingest.py
```

Wait until it finishes (~38 documents). This fills:

- Supabase `documents` table  
- Qdrant collection  
- Local folder `project/indexdir/` (BM25 — needed for Cloud Run)

### 4.4 Verify

```powershell
.\venv\Scripts\python.exe scripts\smoke_api.py
```

(Requires API running locally **or** skip until Cloud Run is up.)

---

## Step 5 — Google Cloud Run (API)

### 5.1 Install Google Cloud CLI

- Download: [cloud.google.com/sdk](https://cloud.google.com/sdk/docs/install)
- Login:

```powershell
gcloud auth login
gcloud auth application-default login
```

### 5.2 Create project, billing, and enable APIs

**Cloud Run requires a billing account** (free tier still needs a card on file — you are not charged unless you exceed free limits).

1. Create or pick a project, then set it active:

```powershell
# New project (optional):
# gcloud projects create YOUR-PROJECT-ID --name="EKIP Knowledge Base"
gcloud config set project YOUR-PROJECT-ID
gcloud auth application-default set-quota-project YOUR-PROJECT-ID
```

2. Link billing: [Google Cloud Console → Billing](https://console.cloud.google.com/billing) → link your project (trial credits are fine).

3. Enable APIs:

```powershell
gcloud services enable run.googleapis.com cloudbuild.googleapis.com artifactregistry.googleapis.com
```

4. **IAM (if Cloud Build push fails with 403):** grant these roles (get `PROJECT_NUMBER` via `gcloud projects describe YOUR-PROJECT-ID --format="value(projectNumber)"`):

| Service account | Roles |
|-----------------|--------|
| `PROJECT_NUMBER@cloudbuild.gserviceaccount.com` | `roles/storage.admin`, `roles/run.admin`, `roles/iam.serviceAccountUser`, `roles/artifactregistry.writer` |
| `PROJECT_NUMBER-compute@developer.gserviceaccount.com` | `roles/artifactregistry.writer`, `roles/logging.logWriter` (optional) |

### 5.3 Build & deploy API (recommended: Cloud Build + image)

From `project/` — **run ingest first** so `indexdir/` exists (BM25 is copied into the image via `Dockerfile`).

**5.3a** Write Cloud Run env from `.env`:

```powershell
.\venv\Scripts\python.exe scripts\write_cloudrun_env.py
```

Creates `deploy/cloudrun.env.yaml` (gitignored).

**5.3b** Build image (`cloudbuild.yaml`, ~8 min):

```powershell
gcloud builds submit . --config cloudbuild.yaml --region europe-west1 --quiet
```

**5.3c** Deploy to Cloud Run:

```powershell
gcloud run deploy kb-api `
  --image europe-west1-docker.pkg.dev/YOUR-PROJECT-ID/cloud-run-source-deploy/kb-api:latest `
  --region europe-west1 `
  --allow-unauthenticated `
  --memory 2Gi `
  --cpu 1 `
  --timeout 300 `
  --min-instances 0 `
  --max-instances 2 `
  --env-vars-file deploy/cloudrun.env.yaml `
  --quiet
```

Use **europe-west1** if your Qdrant cluster is in Europe.

**Important:** **2Gi memory**; first request after idle **30–60s+** (cold start + models). Copy the **Service URL**.

**Alternative:** `gcloud run deploy kb-api --source . …` (same flags). Use **5.3b–5.3c** if builds OOM or time out.

**After Vercel:** set `CORS_ORIGINS` in `.env` (no trailing `/`), then `write_cloudrun_env.py` + `gcloud run services update kb-api --region europe-west1 --env-vars-file deploy/cloudrun.env.yaml --quiet`.

### 5.4 BM25 / `indexdir`

`Dockerfile` copies `indexdir/` from local ingest. If keyword hits fail online: re-run `ingest.py`, then rebuild (5.3b) and redeploy (5.3c).

### 5.5 Test API

```powershell
Invoke-WebRequest -Uri "https://YOUR-SERVICE.run.app/api/health" -UseBasicParsing
```

Expect `"postgres": "up"`, `"qdrant": "up"`.

---

## Step 6 — Vercel (frontend)

### 6.1 Import repo

1. [vercel.com](https://vercel.com) → **Add New Project**.
2. Import **GitHub** → `itikelabhaskar/KB`.
3. **Root Directory:** `project/frontend` (if repo root is BITS_Project parent, set path to `frontend` inside `project` — adjust to match your repo layout).

> Your git root is **`project/`**, so on Vercel set **Root Directory** to `.` if the connected repo is `KB` with backend+frontend at top level, OR monorepo path `frontend` if the whole BITS_Project is the repo.

For repo **`KB`** with structure `backend/`, `frontend/` at root:

- **Root Directory:** `frontend`
- **Framework Preset:** Vite
- **Build Command:** `npm run build`
- **Output Directory:** `dist`

### 6.2 Environment variable

| Name | Value |
|------|--------|
| `VITE_API_URL` | `https://YOUR-SERVICE.run.app` (no trailing slash) |

### 6.3 Deploy

Deploy → note URL: `https://your-app.vercel.app`

### 6.4 Fix CORS on Cloud Run

In `project/.env` (then regenerate yaml — do **not** paste secrets into `gcloud` CLI):

```env
CORS_ORIGINS=https://your-app.vercel.app,http://localhost:5173
```

```powershell
.\venv\Scripts\python.exe scripts\write_cloudrun_env.py
gcloud run services update kb-api --region europe-west1 --env-vars-file deploy/cloudrun.env.yaml --quiet
```

Use the **exact** origin the browser sends (no trailing `/` on the Vercel URL).

---

## Step 7 — End-to-end check

1. Open Vercel URL → login `bhaskar@company.com`.
2. Ask: **What is the PTO policy?**
3. First query after idle may be slow (cold start).
4. Click citation `[1]` → yellow highlights in source panel.
5. **Sources** → **View full document**.

---

## Local development (unchanged)

Friends / you on a new machine:

```powershell
cd project
copy .env.example .env
# Fill GEMINI_API_KEY only; leave DATABASE_URL and QDRANT_URL unset for Docker

docker compose up -d
python -m venv venv
.\venv\Scripts\activate
pip install -r requirements.txt
python scripts\init_db.py
python scripts\build_pdf_corpus.py
python scripts\ingest.py

# Terminal 1 — API
.\venv\Scripts\python.exe -m uvicorn backend.main:app --reload --port 8000

# Terminal 2 — UI
cd frontend
npm install
npm run dev
```

Open http://localhost:5173 — **no `VITE_API_URL` needed** (defaults to `http://localhost:8000`).

### Local vs cloud `.env`

| Variable | Local (Docker) | Cloud |
|----------|----------------|--------|
| `DATABASE_URL` | unset | Supabase URI |
| `QDRANT_URL` | unset | Qdrant Cloud URL |
| `QDRANT_HOST` / `PORT` | `localhost` / `6333` | ignored if `QDRANT_URL` set |
| `VITE_API_URL` | unset (frontend) | Cloud Run URL on Vercel |

You can keep **two files**: `.env` (local) and `.env.cloud` (copy values when running ingest to cloud).

---

## Deploy v1 later (summary)

1. `git checkout v1` → fix if needed → push.
2. New Cloud Run service: `kb-api-v1` from branch `v1`.
3. New Vercel project from branch `v1`.
4. Optional: `QDRANT_COLLECTION=enterprise_docs_v1` + separate ingest.

---

## Troubleshooting

| Problem | Fix |
|---------|-----|
| CORS error in browser | Add exact Vercel URL (no trailing `/`) to `CORS_ORIGINS`, `write_cloudrun_env.py`, update Cloud Run |
| Cloud Build push 403 | Grant `artifactregistry.writer` to compute + cloudbuild service accounts (§5.2) |
| Build OOM / timeout | Use `cloudbuild.yaml` + `E2_HIGHCPU_8`; do not bake models in Dockerfile |
| Artifact Registry prompt | Use `--quiet` or pre-create repo `cloud-run-source-deploy` in `europe-west1` |
| `postgres: down` | Check `DATABASE_URL`, Supabase IP allow, password |
| `qdrant: down` | Check `QDRANT_URL`, `QDRANT_API_KEY`, cluster running |
| LLM unavailable | Gemini quota — add `GEMINI_API_KEY_2` |
| Very slow first search | Free tier cold start — normal |
| No keyword / hybrid results | Redeploy with non-empty `indexdir/` after `ingest.py` |
| Frontend calls localhost | Set `VITE_API_URL` on Vercel, redeploy frontend |

---

## Security checklist

- [ ] Never commit `.env`
- [ ] Rotate `JWT_SECRET` in production
- [ ] Restrict Cloud Run to public only if this is a public demo (class project OK)
- [ ] Rotate Gemini keys if they were ever exposed

---

## Quick reference

| What | URL / command |
|------|----------------|
| Health | `GET /api/health` |
| API docs | `https://YOUR-API.run.app/docs` |
| Smoke test (local API) | `.\venv\Scripts\python.exe scripts\smoke_api.py` |
| Branches | [BRANCHING.md](./BRANCHING.md) |
| Production tests | [PRODUCTION_CHECKLIST.md](./PRODUCTION_CHECKLIST.md) |
