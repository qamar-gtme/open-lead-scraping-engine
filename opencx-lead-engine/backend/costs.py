from __future__ import annotations

import asyncio
from datetime import datetime
from pathlib import Path
from typing import Any

import aiosqlite

DB_PATH = Path(__file__).resolve().parent / "jobs.db"

EXA_PRICING = {
    "search_and_contents": 0.010,
    "find_similar_and_contents": 0.010,
    "get_contents": 0.001,
    "livecrawl": 0.015,
}

OPENAI_PRICING = {
    "gpt-4o": {"input": 0.0000025, "output": 0.000010},
    "gpt-4o-mini": {"input": 0.00000015, "output": 0.0000006},
}

CLAUDE_PRICING = {
    "claude-haiku-4-5": {"input": 0.0000008, "output": 0.000004},
    "claude-sonnet-4-5": {"input": 0.000003, "output": 0.000015},
}


class CostTracker:
    def __init__(self, job_id: str):
        self.job_id = job_id
        self.ledger: list[dict[str, Any]] = []
        self._pending_tasks: list[asyncio.Task] = []

    def log_exa(self, call_type: str, count: int = 1) -> float:
        cost = EXA_PRICING[call_type] * count
        self._append("exa", call_type, None, 0, 0, cost)
        return cost

    def log_openai(self, model: str, tokens_in: int, tokens_out: int) -> float:
        p = OPENAI_PRICING[model]
        cost = (tokens_in * p["input"]) + (tokens_out * p["output"])
        self._append("openai", None, model, tokens_in, tokens_out, cost)
        return cost

    def log_claude(self, model: str, tokens_in: int, tokens_out: int) -> float:
        p = CLAUDE_PRICING[model]
        cost = (tokens_in * p["input"]) + (tokens_out * p["output"])
        self._append("claude", None, model, tokens_in, tokens_out, cost)
        return cost

    def _append(
        self,
        service: str,
        call_type: str | None,
        model: str | None,
        tokens_in: int,
        tokens_out: int,
        cost: float,
    ) -> None:
        self.ledger.append(
            {
                "service": service,
                "call_type": call_type,
                "model": model,
                "tokens_in": tokens_in,
                "tokens_out": tokens_out,
                "cost_usd": cost,
                "ts": datetime.utcnow().isoformat(),
            }
        )
        self.persist_latest()

    async def _persist_latest_async(self) -> None:
        if not self.ledger:
            return
        latest = self.ledger[-1]
        async with aiosqlite.connect(DB_PATH) as db:
            await db.execute(
                """
                INSERT INTO costs (
                    job_id, service, call_type, model, tokens_in,
                    tokens_out, cost_usd, ts
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    self.job_id,
                    latest["service"],
                    latest["call_type"],
                    latest["model"],
                    latest["tokens_in"],
                    latest["tokens_out"],
                    latest["cost_usd"],
                    latest["ts"],
                ),
            )
            await db.commit()

    def persist_latest(self) -> None:
        # Writes the latest ledger entry to jobs.db asynchronously.
        try:
            loop = asyncio.get_running_loop()
        except RuntimeError:
            asyncio.run(self._persist_latest_async())
        else:
            task = loop.create_task(self._persist_latest_async())
            self._pending_tasks.append(task)

    async def flush(self) -> None:
        if not self._pending_tasks:
            return
        pending = [t for t in self._pending_tasks if not t.done()]
        if pending:
            await asyncio.gather(*pending, return_exceptions=True)
        self._pending_tasks = []

    def total(self) -> float:
        return round(sum(e["cost_usd"] for e in self.ledger), 6)

    def by_service(self) -> dict[str, float]:
        out = {"exa": 0.0, "openai": 0.0, "claude": 0.0}
        for e in self.ledger:
            out[e["service"]] += e["cost_usd"]
        return {k: round(v, 6) for k, v in out.items()}


def estimate_cost(config: dict) -> dict:
    regions = config.get("regions", ["NL", "BE"])
    results_per_query = config.get("max_results_per_query", 10)
    enrichers = config.get("enrichers", ["exa_neural", "exa_similar", "exa_keyword"])

    queries_per_region = 8
    similar_anchors = 5
    dedup_factor = 0.6

    neural_calls = len(regions) * queries_per_region if "exa_neural" in enrichers else 0
    similar_calls = similar_anchors if "exa_similar" in enrichers else 0
    keyword_calls = len(regions) * 4 if "exa_keyword" in enrichers else 0
    livecrawl_calls = len(regions) * 4 if "exa_livecrawl" in enrichers else 0

    raw_companies = (neural_calls + similar_calls + keyword_calls) * results_per_query
    unique_companies = int(raw_companies * dedup_factor)
    enrich_calls = unique_companies if "exa_keyword" in enrichers else 0

    exa_cost = (
        neural_calls * EXA_PRICING["search_and_contents"]
        + similar_calls * EXA_PRICING["find_similar_and_contents"]
        + keyword_calls * EXA_PRICING["search_and_contents"]
        + livecrawl_calls * EXA_PRICING["livecrawl"]
        + enrich_calls * EXA_PRICING["search_and_contents"]
    )

    planner_cost = (
        800 * CLAUDE_PRICING["claude-haiku-4-5"]["input"]
        + 600 * CLAUDE_PRICING["claude-haiku-4-5"]["output"]
    )

    q_model = config.get("qualifier_model", "gpt-4o")
    qualifier_cost = unique_companies * (
        700 * OPENAI_PRICING[q_model]["input"] + 200 * OPENAI_PRICING[q_model]["output"]
    )

    total = exa_cost + planner_cost + qualifier_cost

    return {
        "exa_calls": (neural_calls + similar_calls + keyword_calls + livecrawl_calls + enrich_calls),
        "exa_cost_usd": round(exa_cost, 4),
        "ai_calls": unique_companies + 1,
        "ai_cost_usd": round(planner_cost + qualifier_cost, 4),
        "total_estimated_usd": round(total, 4),
        "estimated_companies": unique_companies,
        "confidence": "medium",
    }
