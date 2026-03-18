from __future__ import annotations

import asyncio
from typing import Any

import aiohttp

from outputs.base import OutputMeta, OutputPlugin


class ClayWebhookOutput(OutputPlugin):
    meta = OutputMeta(
        key="webhook_clay",
        name="Clay Webhook",
        description="Sends results row-by-row to Clay-compatible webhook.",
    )

    async def run(self, job_id: str, rows: list[dict[str, Any]], config: dict[str, Any]) -> dict[str, Any]:
        webhook_url = config.get("webhook_url")
        if not webhook_url:
            return {"output": "webhook_clay", "sent": 0, "skipped": True}

        sent = 0
        async with aiohttp.ClientSession() as session:
            for row in rows:
                payload = {"job_id": job_id, "row": row}
                async with session.post(webhook_url, json=payload) as resp:
                    _ = await resp.text()
                    if 200 <= resp.status < 300:
                        sent += 1
                await asyncio.sleep(0.3)
        return {"output": "webhook_clay", "sent": sent}


PLUGIN = ClayWebhookOutput()
