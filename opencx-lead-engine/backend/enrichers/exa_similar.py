from __future__ import annotations

import asyncio
from typing import Any

from exa_py import Exa

from enrichers.base import EnricherMeta, EnricherPlugin, normalize_exa_results


class ExaSimilarEnricher(EnricherPlugin):
    meta = EnricherMeta(
        key="exa_similar",
        name="Exa Similar",
        description="Find similar companies from anchor URLs.",
        cost_per_call_usd=0.010,
        call_type="find_similar_and_contents",
        input_kind="url",
    )

    async def run(self, exa: Exa, item: str, config: dict[str, Any], cost_tracker: Any) -> list[dict[str, Any]]:
        cost_tracker.log_exa(self.meta.call_type, 1)
        response = await asyncio.to_thread(
            exa.find_similar_and_contents,
            item,
            num_results=config.get("max_results_per_query", 10),
            highlights={
                "num_sentences": 6,
                "highlights_per_url": 3,
                "query": "customer support team size agents tickets",
            },
        )
        return normalize_exa_results(response, self.meta.key)


PLUGIN = ExaSimilarEnricher()
