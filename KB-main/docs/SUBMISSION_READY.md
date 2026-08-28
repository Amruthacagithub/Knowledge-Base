# Submission Readiness Checklist

- [ ] Docker running; `ingest.py` completes 38/38 documents
- [ ] `pytest tests/ -m "not integration"` passes
- [ ] `scripts/evaluate.py` passes
- [ ] `npm run build` in `frontend/` passes
- [ ] Manual pass of `docs/TESTING_CHECKLIST.md`
- [ ] `explanation.md` read by team for viva/demo (in parent `BITS_Project/` folder — not in this repo)
- [ ] `phase2_final.md` supervisor section completed
- [ ] v2 live: Vercel + Cloud Run + Supabase + Qdrant (see [DEPLOY.md](./DEPLOY.md))
- [ ] Demo on https://novakb.vercel.app (or your URL) for evaluators
