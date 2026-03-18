from __future__ import annotations

import asyncio
import json
import os
from typing import Any

import anthropic

from costs import CostTracker
from models.base import ModelMeta, ModelPlugin, parse_json_strict

PLANNING_PROMPT = """
You are planning a lead research pipeline for open.cx.
Return ONLY valid JSON:
{
  "neural_queries": ["..."],
  "keyword_queries": ["..."],
  "find_similar_urls": ["https://..."],
  "directory_urls": ["https://..."],
  "livecrawl_queries": ["..."]
}
"""


def _client() -> anthropic.Anthropic:
    api_key = os.getenv("ANTHROPIC_API_KEY")
    if not api_key:
        raise RuntimeError("ANTHROPIC_API_KEY is not set in backend/.env")
    return anthropic.Anthropic(api_key=api_key)


class ClaudeSonnetModel(ModelPlugin):
    meta = ModelMeta(
        key="claude-sonnet-4-5",
        provider="claude",
        name="Claude Sonnet 4.5",
        input_cost_per_token=0.000003,
        output_cost_per_token=0.000015,
    )

    async def plan(
        self,
        prompt: str,
        list_type: str,
        regions: list[str],
        anchors: list[str],
        cost_tracker: CostTracker,
    ) -> dict[str, Any]:
        client = _client()
        response = await asyncio.to_thread(
            client.messages.create,
            model=self.meta.key,
            max_tokens=900,
            system=PLANNING_PROMPT,
            messages=[
                {
                    "role": "user",
                    "content": json.dumps(
                        {
                            "prompt": prompt,
                            "list_type": list_type,
                            "regions": regions,
                            "anchor_urls": anchors,
                        }
                    ),
                }
            ],
        )
        usage = getattr(response, "usage", None)
        cost_tracker.log_claude(
            self.meta.key,
            int(getattr(usage, "input_tokens", 0)),
            int(getattr(usage, "output_tokens", 0)),
        )
        text = response.content[0].text if response.content else "{}"
        return parse_json_strict(text)

    async def qualify(
        self,
        company: dict[str, Any],
        system_prompt: str,
        cost_tracker: CostTracker,
    ) -> dict[str, Any]:
        client = _client()
        response = await asyncio.to_thread(
            client.messages.create,
            model=self.meta.key,
            max_tokens=800,
            system=system_prompt,
            messages=[{"role": "user", "content": json.dumps(company)}],
        )
        usage = getattr(response, "usage", None)
        cost_tracker.log_claude(
            self.meta.key,
            int(getattr(usage, "input_tokens", 0)),
            int(getattr(usage, "output_tokens", 0)),
        )
        text = response.content[0].text if response.content else "{}"
        return parse_json_strict(text)


PLUGIN = ClaudeSonnetModel()
