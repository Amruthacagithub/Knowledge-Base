# Knowledge Base 

**Internal Knowledge Assistant** — A RAG-based search platform that lets employees search across company documents (HR, Engineering, Sales) and get AI-generated answers with citations, respecting their role-based access permissions.

## Features

- **Role-Based Access Control (RBAC):** Users see only what they are allowed to see.
- **Hybrid Search:** Vector (semantic) + BM25 (keyword) with query-type routing.
- **AI Answers:** Google Gemini 2.5 Flash with cited answers `[1]`, `[2]`, …; optional fallback API keys if quota is hit.
- **Professional UI:** Three-pane layout, ChatGPT-style chat, collapsible sources panel, light/dark theme.
- **Document library:** Browse all documents you can access; open full text.
- **PDF support:** 10 PDFs + 28 Markdown files (~38 total); citations include **Page N** for PDFs.
- **Highlights:** Yellow highlighter in source preview and full-document viewer.
- **Admin upload:** Admins can upload `.pdf`, `.md`, or `.txt` from the sidebar (indexed immediately).

---

## Quick Start

### Prerequisites

- **Python 3.10+**, **Node.js 18+**, **Docker Desktop**
- **Google Gemini API Key** — [aistudio.google.com](https://aistudio.google.com/apikey)

### Setup

```powershell
cd project
python -m venv venv
.\venv\Scripts\activate
pip install -r requirements.txt
copy .env.example .env
# Edit .env — set GEMINI_API_KEY (optional GEMINI_API_KEY_2, _3, … for quota fallback)
docker compose up -d
python scripts/init_db.py
python scripts/build_pdf_corpus.py
python scripts/ingest.py
```

### Run

**Backend** (from `project/`):

```powershell
python -m uvicorn backend.main:app --host 0.0.0.0 --port 8000 --reload
```

**Frontend:**

```powershell
cd frontend
npm install
npm run dev
```

Open **http://localhost:5173** — API docs: **http://localhost:8000/docs**

---

## Testing

```powershell
# Unit tests (backend) — use project venv
.\venv\Scripts\python.exe -m pytest tests\ -m "not integration" -q

# Frontend utils
cd frontend
npm run test
npm run build

# API smoke (backend must be running on :8000)
cd ..
.\venv\Scripts\python.exe scripts\smoke_api.py

# Full integration eval (needs Docker + ingest)
$env:PYTHONIOENCODING='utf-8'
.\venv\Scripts\python.exe scripts\evaluate.py
```

See `docs/TESTING_CHECKLIST.md`, `docs/DEMO_SCRIPT.md`, `docs/DATA_STRATEGY.md`.

### Deploy online (v2)

Step-by-step: **[docs/DEPLOY.md](docs/DEPLOY.md)** (Vercel + Cloud Run + Supabase + Qdrant Cloud).  
Git branches (v1 vs v2): **[docs/BRANCHING.md](docs/BRANCHING.md)**.


---

## Demo users

| Email | Role |
|-------|------|
| bhaskar@company.com | Admin (upload documents) |
| amrutha@company.com | HR |
| harshini@company.com | Engineer |
| tanvi@company.com | Sales |
| arijith@company.com | Employee |

---

## Project Structure

```
project/
├── backend/           # FastAPI, RAG pipeline, documents API
├── frontend/          # React + Vite
├── documents/         # manifest.json + HR/Engineering/Sales files
├── scripts/           # ingest, evaluate, build_pdf_corpus
├── tests/             # pytest suite
└── docs/              # Testing checklist, demo script
```

**After changing chunk schema or adding PDFs:** run `python scripts/ingest.py` again (recreates BM25 index).
