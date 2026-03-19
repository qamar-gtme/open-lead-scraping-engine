# Deploy open.cx Lead Engine on Vercel

Deploy as **two Vercel projects**:

1. `backend` (FastAPI serverless)
2. `frontend` (Vite static app)

---

## 1) Deploy backend

Project settings:

- Framework preset: **Other**
- Root directory: `opencx-lead-engine/backend`
- Build/Output commands: leave default for Python

Environment variables:

- `EXA_API_KEY`
- `OPENAI_API_KEY`
- `ANTHROPIC_API_KEY`
- `PARALLEL_API_KEY` (optional, reserved)
- `CORS_ORIGINS` (recommended), example:
  - `https://your-frontend.vercel.app,http://localhost:5173`

This repo includes `backend/vercel.json` routing all paths to `main.py`.

After deploy, note the backend URL:

- `https://your-backend.vercel.app`

Quick test:

```bash
curl https://your-backend.vercel.app/list-types
```

---

## 2) Deploy frontend

Project settings:

- Framework preset: **Vite**
- Root directory: `opencx-lead-engine/frontend`

Environment variables:

- `VITE_API_BASE_URL=https://your-backend.vercel.app`

This repo includes `frontend/vercel.json` for SPA rewrites.

---

## 3) Verify end-to-end

1. Open frontend URL.
2. Enter prompt in Prompt panel.
3. Confirm Suggestion panel auto-fills.
4. Accept suggestion and run.
5. Watch logs/results/costs update.

---

## Notes about serverless limits

- Vercel Python uses a serverless runtime.
- Long-running jobs may hit execution time limits depending on your plan.
- Data path is auto-switched to `/tmp/opencx-lead-engine` on Vercel runtime.
  - This is ephemeral storage and can be cleared between invocations.
- For durable production history/costs/results, move SQLite to a managed DB.
