from __future__ import annotations

from app.models import Lead
from app.providers.base import LeadProvider


class MockLeadProvider(LeadProvider):
    name = "mock"

    def __init__(self) -> None:
        self.dataset = [
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

    async def scrape(self, query: str, limit: int) -> list[Lead]:
        query_terms = {part.lower() for part in query.split() if part.strip()}
        ranked = sorted(
            self.dataset,
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
