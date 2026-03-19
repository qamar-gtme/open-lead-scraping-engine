# Open Lead Scraping Engine

FastAPI lead scraping app with an explicit provider registry (Vercel-safe).

- **Backend**: FastAPI
- **Providers**: explicit plugin registry (`exa`, `mock`) in `app/providers/__init__.py`
- **Frontend**: Plain HTML/CSS/JS served by FastAPI

## Quickstart

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload
```

Open `http://127.0.0.1:8000` in your browser.

## Environment variables

Create `.env` in repo root:

```bash
EXA_API_KEY=your_key_here
SCRAPER_PROVIDERS=exa,mock
REQUIRE_PRIMARY_PROVIDER=1
```

### Required and optional env vars

- `EXA_API_KEY` *(required when `exa` provider is enabled)*
- `SCRAPER_PROVIDERS` *(optional)*: comma-separated provider order, default `exa,mock`
- `REQUIRE_PRIMARY_PROVIDER` *(optional)*:
  - `1` (default): app fails startup if first provider in `SCRAPER_PROVIDERS` is unavailable
  - `0`: allows fallback providers to run even if the first provider is unavailable

## API

### `POST /api/leads/scrape`

Request body:

```json
{
  "query": "b2b dental clinics in texas",
  "limit": 5
}
```

`query` now supports long prompts up to 100,000 characters (multi-page briefs).

### `GET /providers`

Returns provider diagnostics:

- configured provider order
- loaded providers
- reasons unavailable providers were skipped

### `GET /health`

Returns `{ "status": "ok" }`.

## Vercel deployment

Root `vercel.json` routes all `/api/*` requests to `api/index.py`, which exports the FastAPI app:

- `api/index.py` -> `from app.main import app`

After deployment, verify:

```bash
curl https://your-app.vercel.app/providers
curl -X POST https://your-app.vercel.app/api/leads/scrape \
  -H "Content-Type: application/json" \
  -d '{"query":"SaaS companies in NYC","limit":3}'
```
