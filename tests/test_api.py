from fastapi.testclient import TestClient

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
    assert data["provider"] in {"exa", "mock"}
    assert len(data["leads"]) == 3
