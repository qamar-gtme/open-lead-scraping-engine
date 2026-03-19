from app.providers.base import LeadProvider
from app.providers.exa_provider import ExaLeadProvider
from app.providers.mock_provider import MockLeadProvider

# Explicit registry so deployment bundlers (including Vercel) can
# include providers without relying on runtime filesystem scanning.
PROVIDER_REGISTRY: dict[str, type[LeadProvider]] = {
    "exa": ExaLeadProvider,
    "mock": MockLeadProvider,
}

__all__ = ["LeadProvider", "PROVIDER_REGISTRY", "ExaLeadProvider", "MockLeadProvider"]
