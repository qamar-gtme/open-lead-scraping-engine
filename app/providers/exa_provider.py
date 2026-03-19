from __future__ import annotations

import os
from typing import Any

import httpx

from app.models import Lead
from app.providers.base import LeadProvider


class ExaLeadProvider(LeadProvider):
    name = "exa"
    required_env_vars = ("EXA_API_KEY",)

    def __init__(self) -> None:
        self.api_key = os.getenv("EXA_API_KEY")

    async def scrape(self, query: str, limit: int) -> list[Lead]:
        if not self.api_key:
            raise RuntimeError("EXA_API_KEY is missing")

        payload = {
            "query": query,
            "type": "keyword",
            "numResults": limit,
            "contents": {"text": True},
        }
        headers = {"x-api-key": self.api_key, "Content-Type": "application/json"}

        async with httpx.AsyncClient(timeout=20) as client:
            response = await client.post("https://api.exa.ai/search", json=payload, headers=headers)
            response.raise_for_status()
            data = response.json()
        return self._parse_exa_results(data, limit)

    @staticmethod
    def _parse_exa_results(data: dict[str, Any], limit: int) -> list[Lead]:
        results = data.get("results")
        if not isinstance(results, list):
            return []

        leads: list[Lead] = []
        for item in results[:limit]:
            if not isinstance(item, dict):
                continue
            title = str(item.get("title") or "Untitled source")
            url = item.get("url")
            text = str(item.get("text") or "No summary available from source.")
            summary = text.strip().replace("\n", " ")
            if len(summary) > 350:
                summary = f"{summary[:347]}..."
            leads.append(Lead(name=title, website=str(url) if url else None, summary=summary, source="exa"))
        return leads
