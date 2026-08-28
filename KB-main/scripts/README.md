# Scripts

| Script | Purpose |
|--------|---------|
| `init_db.py` | Create tables and seed 5 demo users |
| `build_pdf_corpus.py` | Generate 10 PDFs and append manifest entries |
| `ingest.py` | Full ingest: parse → chunk → Qdrant + BM25 + PostgreSQL |
| `evaluate.py` | Integration eval: permissions, relevance, router, latency |

## Typical order

```powershell
python scripts/init_db.py
python scripts/build_pdf_corpus.py
python scripts/ingest.py
python scripts/evaluate.py
```

## Testing

```powershell
pytest tests/ -m "not integration"
pytest tests/ -m integration
```
