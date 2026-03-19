from __future__ import annotations

from app.provider_registry import ProviderRegistry, parse_provider_order
from app.models import Lead


class NoProviderAvailableError(RuntimeError):
    pass


class LeadScrapeExecutionError(RuntimeError):
    pass


class LeadScraperService:
    def __init__(self, provider_registry: ProviderRegistry | None = None) -> None:
        self.registry = provider_registry or ProviderRegistry(parse_provider_order())

    async def scrape(self, query: str, limit: int) -> tuple[str, list[Lead]]:
        if not self.registry.has_provider:
            diagnostics = self.registry.diagnostics()
            raise NoProviderAvailableError(f"No scraping provider available. {diagnostics}")

        errors: dict[str, str] = {}
        for provider in self.registry.providers:
            try:
                leads = await provider.scrape(query, limit)
                return provider.name, leads
            except Exception as exc:  # pragma: no cover - error path
                errors[provider.name] = str(exc)
                continue

        raise LeadScrapeExecutionError(f"All scraping providers failed: {errors}")
