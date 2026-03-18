from __future__ import annotations

import asyncio
from typing import Any

import aiohttp

from outputs.base import OutputMeta, OutputPlugin


class GenericWebhookOutput(OutputPlugin):
    meta = OutputMeta(
        key="webhook_generic",
        name="Generic Webhook",
        description="Sends each row to an arbitrary webhook endpoint.",
    )

    async def run(self, job_id: str, rows: list[dict[str, Any]], config: dict[str, Any]) -> dict[str, Any]:
        webhook_url = config.get("generic_webhook_url") or config.get("webhook_url")
        if not webhook_url:
            return {"output": "webhook_generic", "sent": 0, "skipped": True}

        sent = 0
        async with aiohttp.ClientSession() as session:
            for row in rows:
                async with session.post(webhook_url, json={"job_id": job_id, "data": row}) as resp:
                    _ = await resp.text()
                    if 200 <= resp.status < 300:
                        sent += 1
                await asyncio.sleep(0.3)
        return {"output": "webhook_generic", "sent": sent}


PLUGIN = GenericWebhookOutput()
