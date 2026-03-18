from __future__ import annotations

import importlib
import pkgutil
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any

DEFAULT_QUALIFIER_SYSTEM_PROMPT = """
You are a senior sales analyst qualifying accounts for
open.cx, a customer support AI platform competing
directly with Intercom.

Best fit:
- Customer support is a core operational function
- High inbound ticket/chat/email volume daily
- Dedicated support agents (not sales doing support)
- 100–5000 employees sweet spot
- Industries: eCommerce, SaaS, Fintech, Neobanks,
  Insurtech, Telco, Logistics, Travel, Utilities
- European HQ

Score 1–100. Return 0 ONLY if clearly irrelevant
(news site, job board, Wikipedia).

Rubric:
90–100: Large dedicated support team confirmed,
        right industry, high volume signals
75–89:  Strong fit, most signals present
60–74:  Probable fit, core ICP match
40–59:  Possible fit, some signals
1–39:   Weak fit, thin signals — include anyway
0:      Clearly irrelevant — discard only

Return ONLY valid JSON, no preamble, no markdown:
{
  "qualifies": true/false,
  "fit_score": 1-100,
  "icp_tier": 1/2/3,
  "company_name": string,
  "domain": string,
  "country": string,
  "city": string or null,
  "industry": string,
  "estimated_total_employees": integer or null,
  "estimated_support_headcount": integer or null,
  "support_signals": [string],
  "risk_flags": [string],
  "fit_reason": "2 sentences max",
  "suggested_angle": "1 sentence outreach angle"
}

Tier: >=75=1, 60-74=2, 1-59=3
"""


@dataclass
class ListTypeMeta:
    key: str
    name: str
    description: str


class ListTypePlugin(ABC):
    meta: ListTypeMeta

    def get_system_prompt(self) -> str:
        return DEFAULT_QUALIFIER_SYSTEM_PROMPT

    @abstractmethod
    def get_anchors(self, regions: list[str]) -> list[str]:
        raise NotImplementedError

    def metadata(self) -> dict[str, Any]:
        return {
            "key": self.meta.key,
            "name": self.meta.name,
            "description": self.meta.description,
        }


def load_plugins() -> dict[str, ListTypePlugin]:
    plugins: dict[str, ListTypePlugin] = {}
    package = __package__ or "lists"
    for module_info in pkgutil.iter_modules(__path__):  # type: ignore[name-defined]
        if module_info.name == "base":
            continue
        module = importlib.import_module(f"{package}.{module_info.name}")
        plugin = getattr(module, "PLUGIN", None)
        if plugin:
            plugins[plugin.meta.key] = plugin
    return plugins


def metadata() -> list[dict[str, Any]]:
    plugins = load_plugins()
    return [plugins[key].metadata() for key in sorted(plugins.keys())]
