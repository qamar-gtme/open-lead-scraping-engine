from __future__ import annotations

import asyncio
import csv
from pathlib import Path
from typing import Any

from outputs.base import OutputMeta, OutputPlugin

EXPORT_DIR = Path(__file__).resolve().parent.parent / "exports"


class CSVWriterOutput(OutputPlugin):
    meta = OutputMeta(
        key="csv_writer",
        name="CSV Export",
        description="Writes qualified companies to CSV in backend/exports.",
    )

    async def run(self, job_id: str, rows: list[dict[str, Any]], config: dict[str, Any]) -> dict[str, Any]:
        EXPORT_DIR.mkdir(parents=True, exist_ok=True)
        path = EXPORT_DIR / f"{job_id}.csv"
        fieldnames = [
            "fit_score",
            "icp_tier",
            "company_name",
            "domain",
            "country",
            "city",
            "industry",
            "estimated_total_employees",
            "estimated_support_headcount",
            "fit_reason",
            "suggested_angle",
            "support_signals",
            "risk_flags",
        ]
        await asyncio.to_thread(_write_csv_sync, path, rows, fieldnames)
        return {"output": "csv", "path": str(path)}


def _write_csv_sync(path: Path, rows: list[dict[str, Any]], fieldnames: list[str]) -> None:
    with path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            payload = {k: row.get(k) for k in fieldnames}
            payload["support_signals"] = "; ".join(row.get("support_signals", []))
            payload["risk_flags"] = "; ".join(row.get("risk_flags", []))
            writer.writerow(payload)


PLUGIN = CSVWriterOutput()
