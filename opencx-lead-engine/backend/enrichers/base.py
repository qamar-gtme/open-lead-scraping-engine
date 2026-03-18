from __future__ import annotations

import importlib
import os
import pkgutil
from abc import ABC, abstractmethod
from dataclasses import dataclass
from pathlib import Path
from typing import Any
from urllib.parse import urlparse

from exa_py import Exa

from costs import EXA_PRICING


def _extract_text_list(value: Any) -> list[str]:
    if isinstance(value, list):
        out: list[str] = []
        for item in value:
            if isinstance(item, str):
                out.append(item)
            elif isinstance(item, dict):
                text_val = item.get("text") or item.get("highlight")
                if text_val:
                    out.append(str(text_val))
        return out
    if isinstance(value, str):
        return [value]
    return []


def normalize_exa_results(raw: Any, source: str) -> list[dict[str, Any]]:
    if hasattr(raw, "results"):
        results = getattr(raw, "results")
    elif isinstance(raw, dict):
        results = raw.get("results", [])
    else:
        results = []

    if not isinstance(results, list):
        return []

    normalized: list[dict[str, Any]] = []
    for item in results:
        if not isinstance(item, dict):
            item = item.__dict__ if hasattr(item, "__dict__") else {}
        url = str(item.get("url") or "")
        if not url:
            continue
        domain = urlparse(url).netloc.lower()
        title = str(item.get("title") or domain or "Unknown")
        highlights = _extract_text_list(item.get("highlights"))
        summary = str(item.get("summary") or item.get("text") or "")
        normalized.append(
            {
                "source": source,
                "url": url,
                "domain": domain,
                "title": title,
                "highlights": highlights,
                "summary": summary,
                "raw": item,
            }
        )
    return normalized


@dataclass
class EnricherMeta:
    key: str
    name: str
    description: str
    cost_per_call_usd: float
    call_type: str
    input_kind: str


class EnricherPlugin(ABC):
    meta: EnricherMeta

    @abstractmethod
    async def run(self, exa: Exa, item: str, config: dict[str, Any], cost_tracker: Any) -> list[dict[str, Any]]:
        raise NotImplementedError

    def metadata(self) -> dict[str, Any]:
        return {
            "key": self.meta.key,
            "name": self.meta.name,
            "description": self.meta.description,
            "cost_per_call_usd": self.meta.cost_per_call_usd,
            "call_type": self.meta.call_type,
            "input_kind": self.meta.input_kind,
        }


def get_exa_client() -> Exa:
    api_key = os.getenv("EXA_API_KEY")
    if not api_key:
        raise RuntimeError("EXA_API_KEY is not set in backend/.env")
    return Exa(api_key=api_key)


def load_plugins() -> dict[str, EnricherPlugin]:
    plugins: dict[str, EnricherPlugin] = {}
    package = __package__ or "enrichers"
    module_dir = Path(__file__).resolve().parent
    for module_info in pkgutil.iter_modules([str(module_dir)]):
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


def cost_for_call_type(call_type: str) -> float:
    return EXA_PRICING[call_type]
