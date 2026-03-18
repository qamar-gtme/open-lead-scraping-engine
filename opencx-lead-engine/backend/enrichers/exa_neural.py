from __future__ import annotations

import asyncio
from typing import Any

from exa_py import Exa

from enrichers.base import EnricherMeta, EnricherPlugin, normalize_exa_results


class ExaNeuralEnricher(EnricherPlugin):
    meta = EnricherMeta(
        key="exa_neural",
        name="Exa Neural Search",
        description="Neural query search with highlights and summary.",
        cost_per_call_usd=0.010,
        call_type="search_and_contents",
        input_kind="query",
    )

    async def run(self, exa: Exa, item: str, config: dict[str, Any], cost_tracker: Any) -> list[dict[str, Any]]:
        cost_tracker.log_exa(self.meta.call_type, 1)
        response = await asyncio.to_thread(
            exa.search_and_contents,
            item,
            type="neural",
            num_results=config.get("max_results_per_query", 10),
            use_autoprompt=True,
            highlights={
                "num_sentences": 6,
                "highlights_per_url": 3,
                "query": "customer support team size agents tickets",
            },
            summary={
                "query": "What does this company do and how big is their support team?",
            },
        )
        return normalize_exa_results(response, self.meta.key)


PLUGIN = ExaNeuralEnricher()
