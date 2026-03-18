from pathlib import Path

from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from app.models import ScrapeRequest, ScrapeResponse
from app.scraper import LeadScraperService

load_dotenv()

app = FastAPI(title="Open Lead Scraping Engine", version="0.1.0")
scraper = LeadScraperService()
static_dir = Path(__file__).parent / "static"

app.mount("/static", StaticFiles(directory=static_dir), name="static")


@app.get("/")
def read_index() -> FileResponse:
    return FileResponse(static_dir / "index.html")


@app.get("/health")
def healthcheck() -> dict[str, str]:
    return {"status": "ok"}


@app.post("/api/leads/scrape", response_model=ScrapeResponse)
async def scrape_leads(payload: ScrapeRequest) -> ScrapeResponse:
    provider, leads = await scraper.scrape(payload.query, payload.limit)
    return ScrapeResponse(query=payload.query, provider=provider, leads=leads)
