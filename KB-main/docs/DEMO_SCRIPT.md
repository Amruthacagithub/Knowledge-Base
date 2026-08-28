# 5-Minute Supervisor Demo Script

## Setup (before meeting)

1. `docker compose up -d`
2. `python scripts/build_pdf_corpus.py` (if PDFs missing)
3. `python scripts/ingest.py`
4. Backend: `python -m uvicorn backend.main:app --port 8000`
5. Frontend: `cd frontend && npm run dev`
6. Open http://localhost:5173

## Demo flow

### 1. Problem (30 sec)

"Employees waste time searching HR, Engineering, and Sales silos. We built one search bar with permissions and cited AI answers."

### 2. Login & chat (1 min)

- Log in as **Amrutha (HR)** — ask **"What is the PTO policy?"**
- Show citation `[1]`, yellow highlight in source panel, **View full document**.

### 3. Permissions (1 min)

- **Harshini (Engineering)** — **"What are the salary bands?"** — restricted HR doc hidden.
- **Bhaskar (Admin)** — same query — sees Compensation Policy.

### 4. PDF & pages (1 min)

- Ask **"What are our pricing tiers?"** (may cite PDF Pricing Tiers).
- Show **Page N** on citation; open full viewer — paginated PDF text + **Open PDF**.

### 5. All sources & library (1 min)

- Click **Sources** in header — all citations from last answer.
- Sidebar **Your documents (38)** — department filter; open any doc.

### 6. Admin upload (45 sec)

- **Bhaskar** — expand **Upload document** — upload a short `.md` file.
- Search for its content — proves live ingestion.

### 7. Engineering depth (30 sec)

- `python scripts/evaluate.py` — all suites PASS.
- `pytest tests/ -m "not integration"` — automated unit tests.
