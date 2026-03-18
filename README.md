# Open Lead Scraping Engine

Minimal web app for finding potential business leads.

- **Backend**: FastAPI
- **Data source**: Exa API (when `EXA_API_KEY` is set), with a mock fallback so the app always works
- **Frontend**: Plain HTML/CSS/JS served by FastAPI

## Quickstart

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload
```

Open `http://127.0.0.1:8000` in your browser.

## Use real Exa data

Create a `.env` file:

```bash
EXA_API_KEY=your_key_here
```

The app will automatically switch from mock data to Exa responses.

## API

### `POST /api/leads/scrape`

Request body:

```json
{
  "query": "b2b dental clinics in texas",
  "limit": 5
}
```

### `GET /health`

Returns `{ "status": "ok" }`.
