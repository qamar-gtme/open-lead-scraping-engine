from __future__ import annotations

import importlib
import pkgutil
from abc import ABC, abstractmethod
from dataclasses import dataclass
from pathlib import Path
from typing import Any


@dataclass
class OutputMeta:
    key: str
    name: str
    description: str


class OutputPlugin(ABC):
    meta: OutputMeta

    @abstractmethod
    async def run(self, job_id: str, rows: list[dict[str, Any]], config: dict[str, Any]) -> dict[str, Any]:
        raise NotImplementedError

    def metadata(self) -> dict[str, str]:
        return {
            "key": self.meta.key,
            "name": self.meta.name,
            "description": self.meta.description,
        }


def load_plugins() -> dict[str, OutputPlugin]:
    plugins: dict[str, OutputPlugin] = {}
    package = __package__ or "outputs"
    module_dir = Path(__file__).resolve().parent
    for module_info in pkgutil.iter_modules([str(module_dir)]):
        if module_info.name == "base":
            continue
        module = importlib.import_module(f"{package}.{module_info.name}")
        plugin = getattr(module, "PLUGIN", None)
        if plugin:
            plugins[plugin.meta.key] = plugin
    return plugins


def metadata() -> list[dict[str, str]]:
    plugins = load_plugins()
    return [plugins[key].metadata() for key in sorted(plugins.keys())]
