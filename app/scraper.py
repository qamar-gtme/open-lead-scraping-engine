from __future__ import annotations

import os
from typing import Any

import httpx

from app.models import Lead


class LeadScraperService:
    def __init__(self, exa_api_key: str | None = None) -> None:
        self.exa_api_key = exa_api_key or os.getenv("EXA_API_KEY")

    async def scrape(self, query: str, limit: int) -> tuple[str, list[Lead]]:
        if self.exa_api_key:
            exa_results = await self._scrape_with_exa(query, limit)
            if exa_results:
                return "exa", exa_results

        return "mock", self._scrape_with_mock_data(query, limit)

    async def _scrape_with_exa(self, query: str, limit: int) -> list[Lead]:
        payload = {
            "query": query,
            "type": "keyword",
            "numResults": limit,
            "contents": {"text": True},
        }
        headers = {"x-api-key": self.exa_api_key or "", "Content-Type": "application/json"}

        try:
            async with httpx.AsyncClient(timeout=20) as client:
                response = await client.post("https://api.exa.ai/search", json=payload, headers=headers)
                response.raise_for_status()
                data = response.json()
        except (httpx.HTTPError, ValueError):
            return []

        return self._parse_exa_results(data, limit)

    def _parse_exa_results(self, data: dict[str, Any], limit: int) -> list[Lead]:
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
            if len(summary) > 240:
                summary = f"{summary[:237]}..."
            leads.append(Lead(name=title, website=str(url) if url else None, summary=summary, source="exa"))
        return leads

    def _scrape_with_mock_data(self, query: str, limit: int) -> list[Lead]:
        dataset = [
            {
                "name": "ClearTrail Logistics",
                "website": "https://cleartrail.example.com",
                "summary": "Regional logistics company expanding B2B freight operations.",
            },
            {
                "name": "Northpeak Dental Group",
                "website": "https://northpeakdental.example.com",
                "summary": "Multi-location dental clinics looking for patient growth tools.",
            },
            {
                "name": "SignalFrame SaaS",
                "website": "https://signalframe.example.com",
                "summary": "B2B software startup hiring outbound sales representatives.",
            },
            {
                "name": "Horizon Home Services",
                "website": "https://horizonhomeservices.example.com",
                "summary": "Residential maintenance business focused on recurring contracts.",
            },
            {
                "name": "Ridgeway Legal Partners",
                "website": "https://ridgewaylegal.example.com",
                "summary": "Small law firm modernizing lead intake and CRM workflows.",
            },
            {
                "name": "Atlas Industrial Supply",
                "website": "https://atlasindustrial.example.com",
                "summary": "Distributor targeting manufacturing clients across three states.",
            },
            {
                "name": "Brightline Renovations",
                "website": "https://brightlinerenovations.example.com",
                "summary": "Home renovation team growing via local search and referrals.",
            },
        ]

        query_terms = {part.lower() for part in query.split() if part.strip()}
        ranked = sorted(
            dataset,
            key=lambda row: self._query_score(query_terms, row["name"], row["summary"]),
            reverse=True,
        )

        leads: list[Lead] = []
        for row in ranked[:limit]:
            leads.append(
                Lead(
                    name=row["name"],
                    website=row["website"],
                    summary=row["summary"],
                    source="mock",
                )
            )
        return leads

    @staticmethod
    def _query_score(query_terms: set[str], name: str, summary: str) -> int:
        if not query_terms:
            return 0
        corpus = f"{name} {summary}".lower()
        return sum(1 for term in query_terms if term in corpus)
