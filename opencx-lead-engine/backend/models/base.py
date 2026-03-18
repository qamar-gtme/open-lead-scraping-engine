from __future__ import annotations

import importlib
import json
import pkgutil
from abc import ABC, abstractmethod
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from costs import CLAUDE_PRICING, OPENAI_PRICING


@dataclass
class ModelMeta:
    key: str
    provider: str
    name: str
    input_cost_per_token: float
    output_cost_per_token: float
    supports_planning: bool = True
    supports_qualification: bool = True


def parse_json_strict(text: str) -> dict[str, Any]:
    text = text.strip()
    if not text:
        raise ValueError("Empty model output")
    start = text.find("{")
    end = text.rfind("}")
    if start >= 0 and end > start:
        text = text[start : end + 1]
    return json.loads(text)


class ModelPlugin(ABC):
    meta: ModelMeta

    @abstractmethod
    async def plan(
        self,
        prompt: str,
        list_type: str,
        regions: list[str],
        anchors: list[str],
        cost_tracker: Any,
    ) -> dict[str, Any]:
        raise NotImplementedError

    @abstractmethod
    async def qualify(
        self,
        company: dict[str, Any],
        system_prompt: str,
        cost_tracker: Any,
    ) -> dict[str, Any]:
        raise NotImplementedError

    def metadata(self) -> dict[str, Any]:
        return {
            "key": self.meta.key,
            "provider": self.meta.provider,
            "name": self.meta.name,
            "input_cost_per_token": self.meta.input_cost_per_token,
            "output_cost_per_token": self.meta.output_cost_per_token,
            "supports_planning": self.meta.supports_planning,
            "supports_qualification": self.meta.supports_qualification,
        }


def load_plugins() -> dict[str, ModelPlugin]:
    plugins: dict[str, ModelPlugin] = {}
    package = __package__ or "models"
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


def default_model_metadata() -> list[dict[str, Any]]:
    return [
        {
            "key": "gpt-4o",
            "provider": "openai",
            "name": "GPT-4o",
            "input_cost_per_token": OPENAI_PRICING["gpt-4o"]["input"],
            "output_cost_per_token": OPENAI_PRICING["gpt-4o"]["output"],
        },
        {
            "key": "gpt-4o-mini",
            "provider": "openai",
            "name": "GPT-4o mini",
            "input_cost_per_token": OPENAI_PRICING["gpt-4o-mini"]["input"],
            "output_cost_per_token": OPENAI_PRICING["gpt-4o-mini"]["output"],
        },
        {
            "key": "claude-haiku-4-5",
            "provider": "claude",
            "name": "Claude Haiku 4.5",
            "input_cost_per_token": CLAUDE_PRICING["claude-haiku-4-5"]["input"],
            "output_cost_per_token": CLAUDE_PRICING["claude-haiku-4-5"]["output"],
        },
        {
            "key": "claude-sonnet-4-5",
            "provider": "claude",
            "name": "Claude Sonnet 4.5",
            "input_cost_per_token": CLAUDE_PRICING["claude-sonnet-4-5"]["input"],
            "output_cost_per_token": CLAUDE_PRICING["claude-sonnet-4-5"]["output"],
        },
    ]
