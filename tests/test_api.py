import os

from fastapi.testclient import TestClient

# Use mock provider for deterministic tests.
os.environ["SCRAPER_PROVIDERS"] = "mock"
os.environ["REQUIRE_PRIMARY_PROVIDER"] = "0"

from app.main import app

client = TestClient(app)


def test_healthcheck() -> None:
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_scrape_endpoint_returns_leads() -> None:
    response = client.post("/api/leads/scrape", json={"query": "b2b software startup", "limit": 3})
    data = response.json()

    assert response.status_code == 200
    assert data["query"] == "b2b software startup"
    assert data["provider"] == "mock"
    assert len(data["leads"]) == 3


def test_provider_diagnostics_endpoint() -> None:
    response = client.get("/providers")
    payload = response.json()
    assert response.status_code == 200
    assert payload["loaded_providers"] == ["mock"]


def test_scrape_accepts_long_prompt() -> None:
    long_query = "SaaS support companies. " * 500
    response = client.post("/api/leads/scrape", json={"query": long_query, "limit": 2})
    assert response.status_code == 200
    assert response.json()["query"] == long_query
