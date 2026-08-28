# Testing Checklist

## Automated (run before demo/submission)

```powershell
cd project
.\venv\Scripts\pip.exe install -r requirements.txt
.\venv\Scripts\python.exe -m pytest tests\ -m "not integration" -q
```

```powershell
cd frontend
npm install
npm run test
npm run build
```

```powershell
cd project
$env:PYTHONIOENCODING='utf-8'
docker compose up -d
.\venv\Scripts\python.exe scripts\ingest.py
.\venv\Scripts\python.exe scripts\evaluate.py
.\venv\Scripts\python.exe -m pytest tests\ -m integration -q
```

Expected: pytest and evaluate exit code 0.

## Infrastructure

- [ ] `docker compose up -d` — Postgres and Qdrant running
- [ ] `GET http://localhost:8000/api/health` — `postgres: up`, `qdrant: up`

## UI manual (http://localhost:5173)

### Login
- [ ] Split-screen login; demo accounts work
- [ ] Theme toggle top-right on chat page

### Chat
- [ ] Input clears on send; typing indicator; markdown renders
- [ ] Citation pills `[1]` open single-source panel with yellow highlight
- [ ] **Sources** button shows all citations from last answer
- [ ] **View full document ↗** opens modal with highlights
- [ ] Chat input stays fixed at bottom while scrolling messages

### PDF & pages
- [ ] Ask question that cites a **(PDF)** document (e.g. pricing after re-ingest)
- [ ] Citation shows **Page N** badge
- [ ] Full viewer shows paginated PDF sections; **Open PDF** works (Admin token)

### Document library
- [ ] Sidebar lists document count (~38 after full ingest)
- [ ] PDF badge on PDF titles; open document from list

### Admin upload (Bhaskar)
- [ ] **Upload document (Admin)** in sidebar
- [ ] Upload small `.md` file — success message; appears in library
- [ ] Search finds uploaded content

### Permissions
- [ ] Harshini — "salary bands" — no Compensation Policy
- [ ] Bhaskar — same query — sees restricted content

## Data

- [ ] `build_pdf_corpus.py` — 10 PDFs in manifest
- [ ] `ingest.py` reports 38/38 documents
- [ ] Chunk count ≥ 80 after full ingest
