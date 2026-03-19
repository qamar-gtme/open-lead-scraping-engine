from __future__ import annotations

from abc import ABC, abstractmethod

from app.models import Lead


class LeadProvider(ABC):
    name: str
    required_env_vars: tuple[str, ...] = ()

    @abstractmethod
    async def scrape(self, query: str, limit: int) -> list[Lead]:
        raise NotImplementedError
