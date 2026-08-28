# Git branches — v1 vs v2

Use **one GitHub repo**: `https://github.com/itikelabhaskar/KB.git`

## Recommended layout

| Branch | Purpose | Deploy now? |
|--------|---------|-------------|
| **`main`** | Current v2 work (full PoC) | **Yes** — this is what you deploy |
| **`v1`** | Frozen original PoC (GitHub snapshot) | **Later** — optional second deploy |

## One-time: create the `v1` branch (keeps old code safe)

Run once from `project/` (does **not** change your local files on `main`):

```powershell
git fetch origin
git branch v1 origin/main
git push -u origin v1
```

- `v1` = exactly what was on GitHub before v2 (initial PoC + readme edit).
- You can fix typos on `v1` later without touching `main`.

## Daily work (v2)

```powershell
git checkout main
# edit, test locally
git add .
git commit -m "Describe change"
git push origin main
```

Vercel / Cloud Run should track **`main`** for the live v2 site.

## Later: deploy v1 as a second website

1. Deploy API: Cloud Run service `kb-api-v1` from branch `v1`.
2. Deploy UI: second Vercel project (or Preview) from branch `v1`.
3. Use separate `QDRANT_COLLECTION=enterprise_docs_v1` if you do not want v1/v2 sharing vectors.

See [DEPLOY.md](./DEPLOY.md) — repeat deploy steps with branch `v1` and different service names.
