from __future__ import annotations

import asyncio
from typing import Any

from exa_py import Exa

from enrichers.base import EnricherMeta, EnricherPlugin, normalize_exa_results


class ExaKeywordEnricher(EnricherPlugin):
    meta = EnricherMeta(
        key="exa_keyword",
        name="Exa Keyword",
        description="Keyword-based discovery and enrichment queries.",
        cost_per_call_usd=0.010,
        call_type="search_and_contents",
        input_kind="query",
    )

    async def run(self, exa: Exa, item: str, config: dict[str, Any], cost_tracker: Any) -> list[dict[str, Any]]:
        cost_tracker.log_exa(self.meta.call_type, 1)
        response = await asyncio.to_thread(
            exa.search_and_contents,
            item,
            type="keyword",
            num_results=config.get("max_results_per_query", 10),
            highlights={
                "num_sentences": 5,
                "highlights_per_url": 2,
                "query": "support team headcount hiring agents",
            },
        )
        return normalize_exa_results(response, self.meta.key)


PLUGIN = ExaKeywordEnricher()
