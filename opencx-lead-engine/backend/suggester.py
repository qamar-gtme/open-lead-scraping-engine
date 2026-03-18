from __future__ import annotations

import asyncio
import json
import os

import anthropic


async def suggest(prompt: str) -> dict:
    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        raise RuntimeError("ANTHROPIC_API_KEY is not set in backend/.env")

    client = anthropic.Anthropic(api_key=api_key)
    response = await asyncio.to_thread(
        client.messages.create,
        model="claude-haiku-4-5",
        max_tokens=800,
        messages=[
            {
                "role": "user",
                "content": f"""
You configure a lead generation pipeline for open.cx,
an Intercom competitor selling to companies with large
customer support teams.

User's prompt: "{prompt}"

Based on this, return the optimal pipeline config.
Respond ONLY in valid JSON, no preamble, no markdown:
{{
  "list_type": "high_volume|partners|bpos",
  "regions": ["NL","BE","DACH","Nordics"],
  "enrichers": ["exa_neural","exa_similar",
                "exa_keyword","exa_contents",
                "exa_livecrawl"],
  "anchor_urls": ["https://..."],
  "planner_model": "claude-haiku-4-5",
  "qualifier_model": "gpt-4o",
  "reasoning": "2 sentences explaining your choices",
  "estimated_results": "X–Y companies"
}}

Enricher selection logic:
- exa_neural: always include
- exa_similar: include if user mentions specific
  company types or industries
- exa_keyword: include for Dutch/German/Nordic queries
- exa_contents: include if user mentions directories
  or specific pages to scrape
- exa_livecrawl: ONLY if user mentions finding current
  tool users or very recent signals

Anchor URLs: 3–5 known companies matching the description.
                """,
            }
        ],
    )
    content = response.content[0].text if response.content else "{}"
    return _parse_json_content(content)


def _parse_json_content(content: str) -> dict:
    text = content.strip()
    if not text:
        raise ValueError("Empty Claude response")
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        start = text.find("{")
        end = text.rfind("}")
        if start >= 0 and end > start:
            return json.loads(text[start : end + 1])
        raise
