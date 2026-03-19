from pathlib import Path

from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from app.provider_registry import require_primary_provider
from app.models import ScrapeRequest, ScrapeResponse
from app.scraper import LeadScrapeExecutionError, LeadScraperService, NoProviderAvailableError

load_dotenv()

app = FastAPI(title="Open Lead Scraping Engine", version="0.1.0")
scraper = LeadScraperService()
static_dir = Path(__file__).parent / "static"

app.mount("/static", StaticFiles(directory=static_dir), name="static")

if not scraper.registry.has_provider:
    diagnostics = scraper.registry.diagnostics()
    raise RuntimeError(f"No scraping provider available at startup. {diagnostics}")

if require_primary_provider() and not scraper.registry.has_primary_provider:
    diagnostics = scraper.registry.diagnostics()
    raise RuntimeError(
        "Primary scraping provider is unavailable. "
        "Set required environment variables or adjust SCRAPER_PROVIDERS. "
        f"{diagnostics}"
    )


@app.get("/")
def read_index() -> FileResponse:
    return FileResponse(static_dir / "index.html")


@app.get("/health")
def healthcheck() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/providers")
def provider_status() -> dict[str, object]:
    return scraper.registry.diagnostics()


@app.post("/api/leads/scrape", response_model=ScrapeResponse)
async def scrape_leads(payload: ScrapeRequest) -> ScrapeResponse:
    try:
        provider, leads = await scraper.scrape(payload.query, payload.limit)
    except NoProviderAvailableError as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc
    except LeadScrapeExecutionError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc
    return ScrapeResponse(query=payload.query, provider=provider, leads=leads)
