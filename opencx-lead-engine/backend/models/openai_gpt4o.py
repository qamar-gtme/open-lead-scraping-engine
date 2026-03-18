from __future__ import annotations

import json
import os
from typing import Any

from openai import AsyncOpenAI

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


def _client() -> AsyncOpenAI:
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise RuntimeError("OPENAI_API_KEY is not set in backend/.env")
    return AsyncOpenAI(api_key=api_key)


class OpenAIGpt4oModel(ModelPlugin):
    meta = ModelMeta(
        key="gpt-4o",
        provider="openai",
        name="GPT-4o",
        input_cost_per_token=0.0000025,
        output_cost_per_token=0.000010,
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
        response = await client.chat.completions.create(
            model=self.meta.key,
            temperature=0.1,
            response_format={"type": "json_object"},
            messages=[
                {"role": "system", "content": PLANNING_PROMPT},
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
                },
            ],
        )
        usage = response.usage
        cost_tracker.log_openai(
            self.meta.key,
            int(usage.prompt_tokens if usage else 0),
            int(usage.completion_tokens if usage else 0),
        )
        text = response.choices[0].message.content or "{}"
        return parse_json_strict(text)

    async def qualify(
        self,
        company: dict[str, Any],
        system_prompt: str,
        cost_tracker: CostTracker,
    ) -> dict[str, Any]:
        client = _client()
        response = await client.chat.completions.create(
            model=self.meta.key,
            temperature=0.0,
            response_format={"type": "json_object"},
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": json.dumps(company)},
            ],
        )
        usage = response.usage
        cost_tracker.log_openai(
            self.meta.key,
            int(usage.prompt_tokens if usage else 0),
            int(usage.completion_tokens if usage else 0),
        )
        text = response.choices[0].message.content or "{}"
        return parse_json_strict(text)


PLUGIN = OpenAIGpt4oModel()
