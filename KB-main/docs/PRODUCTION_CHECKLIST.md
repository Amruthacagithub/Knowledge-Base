# Production checklist

Run before deploying or submitting.

## 1. Infrastructure

```powershell
cd project
docker compose up -d
.\venv\Scripts\python.exe scripts\init_db.py
.\venv\Scripts\python.exe scripts\build_pdf_corpus.py
.\venv\Scripts\python.exe scripts\ingest.py
```

- [ ] `GET /api/health` → `postgres: up`, `qdrant: up`
- [ ] `.env` has `GEMINI_API_KEY` (add `GEMINI_API_KEY_2`, `_3`, … if you need quota fallback)
- [ ] Use **project venv** for Python (`.\venv\Scripts\python.exe`), not global Python

## 2. Automated tests

```powershell
.\venv\Scripts\python.exe -m pytest tests\ -m "not integration" -q
cd frontend
npm run test
npm run build
.\venv\Scripts\python.exe scripts\smoke_api.py   # backend running
```

## 3. Core features (manual)

| # | Feature | How to verify |
|---|---------|----------------|
| 1 | **Login / logout** | Demo emails in README; invalid email rejected |
| 2 | **RBAC** | Harshini: no compensation in results; Bhaskar: can see restricted HR |
| 3 | **Hybrid search + chat** | Ask PTO question; answer + latency metadata |
| 4 | **Citations** | `[1]` pills in answer; click opens source panel |
| 5 | **Source highlights** | Yellow blocks on cited lines (e.g. cash-out) |
| 6 | **All sources panel** | **Sources** button lists citations from last answer |
| 7 | **Full document viewer** | **View full document** → modal + yellow sections |
| 8 | **PDF + page badge** | Cite a PDF; **Page N** badge; **Open PDF** works |
| 9 | **Document library** | Sidebar count ~38; list collapsed by default; open doc |
| 10 | **Department filter** | HR / Engineering / Sales scope |
| 11 | **Admin upload** | Bhaskar: upload `.md`; appears in library + searchable |
| 12 | **Theme** | System default; toggle Light/Dark; header buttons same size |
| 13 | **New conversation** | Clears chat and sources panel |

## 4. Gemini API keys

- **Primary:** `GEMINI_API_KEY` (required)
- **Optional fallbacks:** `GEMINI_API_KEY_2`, `GEMINI_API_KEY_3`, … — on quota/rate-limit (429), the backend tries the next key automatically.
- If **all** keys fail, answers still include **citations [1]…[N]** from search results.

Restart the backend after changing `.env`.

## 5. Production build

```powershell
cd frontend
npm run build
# Serve dist/ behind nginx or `npm run preview`
# Backend: uvicorn without --reload, workers as needed
```

## 6. Cloud production (v2 live)

See **[DEPLOY.md](./DEPLOY.md)** for full steps. Quick verify:

- [ ] https://novakb.vercel.app — login + search works
- [ ] `GET https://kb-api-181317080469.europe-west1.run.app/api/health` → postgres + qdrant up
- [ ] Vercel env `VITE_API_URL` = Cloud Run URL (no trailing slash)
- [ ] `CORS_ORIGINS` on Cloud Run includes Vercel URL (no trailing slash)
- [ ] `JWT_SECRET` set in `.env` + Cloud Run (not default `ekip-prod-change-me`)
- [ ] `.env` never committed; rotate keys if exposed in chat/logs
