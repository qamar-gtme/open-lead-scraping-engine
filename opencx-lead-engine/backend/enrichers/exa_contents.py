from __future__ import annotations

import asyncio
from typing import Any

from exa_py import Exa

from enrichers.base import EnricherMeta, EnricherPlugin, normalize_exa_results


class ExaContentsEnricher(EnricherPlugin):
    meta = EnricherMeta(
        key="exa_contents",
        name="Exa Contents",
        description="Direct content extraction from directory URLs.",
        cost_per_call_usd=0.001,
        call_type="get_contents",
        input_kind="url",
    )

    async def run(self, exa: Exa, item: str, config: dict[str, Any], cost_tracker: Any) -> list[dict[str, Any]]:
        cost_tracker.log_exa(self.meta.call_type, 1)
        response = await asyncio.to_thread(
            exa.get_contents,
            [item],
            highlights={
                "num_sentences": 5,
                "query": "partner reseller implementation consulting",
            },
        )
        return normalize_exa_results(response, self.meta.key)


PLUGIN = ExaContentsEnricher()
