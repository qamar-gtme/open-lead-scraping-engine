from __future__ import annotations

import os

from app.providers import PROVIDER_REGISTRY, LeadProvider

DEFAULT_PROVIDER_ORDER = ("exa", "mock")


def parse_provider_order() -> list[str]:
    configured = os.getenv("SCRAPER_PROVIDERS")
    if not configured:
        return list(DEFAULT_PROVIDER_ORDER)
    return [name.strip() for name in configured.split(",") if name.strip()]


class ProviderRegistry:
    def __init__(self, provider_order: list[str]) -> None:
        self.provider_order = provider_order
        self.providers: list[LeadProvider] = []
        self.unavailable_reasons: dict[str, str] = {}
        self._load()

    def _load(self) -> None:
        for name in self.provider_order:
            provider_cls = PROVIDER_REGISTRY.get(name)
            if not provider_cls:
                self.unavailable_reasons[name] = "Provider is not registered."
                continue

            missing = [env_name for env_name in provider_cls.required_env_vars if not os.getenv(env_name)]
            if missing:
                self.unavailable_reasons[name] = f"Missing environment variables: {', '.join(missing)}"
                continue

            self.providers.append(provider_cls())

    @property
    def has_provider(self) -> bool:
        return bool(self.providers)

    @property
    def primary_provider_name(self) -> str | None:
        return self.providers[0].name if self.providers else None

    @property
    def has_primary_provider(self) -> bool:
        if not self.provider_order:
            return False
        if not self.providers:
            return False
        return self.providers[0].name == self.provider_order[0]

    def diagnostics(self) -> dict[str, object]:
        return {
            "configured_order": self.provider_order,
            "loaded_providers": [provider.name for provider in self.providers],
            "unavailable_reasons": self.unavailable_reasons,
        }


def require_primary_provider() -> bool:
    return os.getenv("REQUIRE_PRIMARY_PROVIDER", "1").strip() != "0"
