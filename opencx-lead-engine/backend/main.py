from __future__ import annotations

import asyncio
import json
import uuid
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Any

import aiosqlite
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from pydantic import BaseModel, Field

from costs import estimate_cost
from db import (
    DB_PATH,
    append_log,
    create_job,
    create_tables,
    get_cost_rows_for_job,
    get_cost_totals,
    get_history,
    get_job,
    get_job_logs,
    get_results,
    mark_cancel_requested,
)
from engine import run_pipeline
from enrichers.base import metadata as enricher_metadata
from lists.base import metadata as list_metadata
from models.base import metadata as model_metadata
from outputs.base import load_plugins as load_output_plugins
from outputs.base import metadata as output_metadata
from suggester import suggest

load_dotenv(Path(__file__).resolve().parent / ".env")


class RunConfig(BaseModel):
    prompt: str = Field(min_length=4)
    list_type: str = Field(default="high_volume")
    regions: list[str] = Field(default_factory=lambda: ["NL", "BE"])
    enrichers: list[str] = Field(default_factory=lambda: ["exa_neural", "exa_similar", "exa_keyword"])
    anchor_urls: list[str] = Field(default_factory=list)
    planner_model: str = Field(default="claude-haiku-4-5")
    qualifier_model: str = Field(default="gpt-4o")
    max_results_per_query: int = Field(default=10, ge=5, le=20)
    outputs: list[str] = Field(default_factory=lambda: ["csv_writer"])
    webhook_url: str | None = None
    hubspot_webhook_url: str | None = None
    generic_webhook_url: str | None = None


class SuggestBody(BaseModel):
    prompt: str = Field(min_length=4)


@asynccontextmanager
async def lifespan(_: FastAPI):
    await create_tables()
    yield


app = FastAPI(title="open.cx lead engine", version="1.0.0", lifespan=lifespan)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
async def root() -> dict[str, str]:
    return {"service": "open.cx lead engine", "status": "ok"}


@app.post("/run")
async def run_job(config: RunConfig) -> dict[str, Any]:
    job_id = str(uuid.uuid4())
    payload = config.model_dump()
    await create_job(job_id, payload)
    await append_log(job_id, "Job created", "gray")
    asyncio.create_task(run_pipeline(job_id, payload))
    return {"job_id": job_id, "status": "queued"}


@app.get("/status/{job_id}")
async def status(job_id: str) -> dict[str, Any]:
    job = await get_job(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")

    logs = await get_job_logs(job_id, limit=300)
    costs = await _job_cost_breakdown(job_id)

    return {
        "job_id": job_id,
        "phase": job["status"],
        "counts": {"companies_found": job["companies_found"]},
        "costs": costs,
        "live_logs": logs,
    }


@app.get("/results/{job_id}")
async def results(job_id: str) -> dict[str, Any]:
    job = await get_job(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    rows = await get_results(job_id)
    return {
        "job_id": job_id,
        "status": job["status"],
        "total_cost_usd": job["total_cost_usd"],
        "companies_found": job["companies_found"],
        "results": rows,
    }


@app.get("/download/{job_id}")
async def download(job_id: str) -> FileResponse:
    path = Path(__file__).resolve().parent / "exports" / f"{job_id}.csv"
    if not path.exists():
        raise HTTPException(status_code=404, detail="CSV not found")
    return FileResponse(path, media_type="text/csv", filename=f"{job_id}.csv")


@app.delete("/job/{job_id}")
async def cancel_job(job_id: str) -> dict[str, Any]:
    job = await get_job(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    if job["status"] in {"completed", "failed", "cancelled"}:
        return {"job_id": job_id, "status": job["status"]}
    await mark_cancel_requested(job_id)
    await append_log(job_id, "Cancel requested by user", "yellow")
    return {"job_id": job_id, "status": "cancel_requested"}


@app.get("/list-types")
async def get_list_types() -> list[dict[str, Any]]:
    return list_metadata()


@app.get("/enrichers")
async def get_enrichers() -> list[dict[str, Any]]:
    return enricher_metadata()


@app.get("/models")
async def get_models() -> list[dict[str, Any]]:
    return model_metadata()


@app.get("/outputs")
async def get_outputs() -> list[dict[str, Any]]:
    return output_metadata()


@app.post("/suggest")
async def suggest_config(body: SuggestBody) -> dict[str, Any]:
    try:
        data = await suggest(body.prompt)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc
    return data


@app.get("/costs/estimate")
async def costs_estimate(
    prompt: str = "",
    list_type: str = "high_volume",
    regions: str = "NL,BE",
    enrichers: str = "exa_neural,exa_similar,exa_keyword",
    anchor_urls: str = "",
    planner_model: str = "claude-haiku-4-5",
    qualifier_model: str = "gpt-4o",
    max_results_per_query: int = Query(default=10, ge=5, le=20),
    outputs: str = "csv_writer",
) -> dict[str, Any]:
    config = {
        "prompt": prompt,
        "list_type": list_type,
        "regions": _split_csv(regions),
        "enrichers": _split_csv(enrichers),
        "anchor_urls": _split_csv(anchor_urls),
        "planner_model": planner_model,
        "qualifier_model": qualifier_model,
        "max_results_per_query": max_results_per_query,
        "outputs": _split_csv(outputs),
    }
    return estimate_cost(config)


@app.get("/costs/total")
async def costs_total() -> dict[str, Any]:
    return await get_cost_totals()


@app.get("/costs/job/{job_id}")
async def costs_job(job_id: str) -> dict[str, Any]:
    rows = await get_cost_rows_for_job(job_id)
    if not rows:
        job = await get_job(job_id)
        if not job:
            raise HTTPException(status_code=404, detail="Job not found")
    exa = round(sum(float(r["cost_usd"]) for r in rows if r["service"] == "exa"), 6)
    openai = round(sum(float(r["cost_usd"]) for r in rows if r["service"] == "openai"), 6)
    claude = round(sum(float(r["cost_usd"]) for r in rows if r["service"] == "claude"), 6)
    total = round(exa + openai + claude, 6)
    job = await get_job(job_id)
    companies = int((job or {}).get("companies_found", 0))
    cpc = round(total / companies, 6) if companies else 0.0
    return {
        "exa_usd": exa,
        "openai_usd": openai,
        "claude_usd": claude,
        "total_usd": total,
        "companies_found": companies,
        "cost_per_company": cpc,
    }


@app.get("/history")
async def history(limit: int = Query(default=50, ge=1, le=200)) -> list[dict[str, Any]]:
    return await get_history(limit=limit)


@app.post("/resend-webhook/{job_id}")
async def resend_webhook(job_id: str, webhook_url: str | None = None) -> dict[str, Any]:
    job = await get_job(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    rows = await get_results(job_id)
    if not rows:
        raise HTTPException(status_code=400, detail="No results for this job")

    config = dict(job.get("config_json", {}))
    if webhook_url:
        config["webhook_url"] = webhook_url

    plugins = load_output_plugins()
    keys = [k for k in ["webhook_clay", "webhook_hubspot", "webhook_generic"] if k in plugins]
    tasks = [plugins[key].run(job_id, rows, config) for key in keys]
    results = await asyncio.gather(*tasks, return_exceptions=True)

    out = []
    for item in results:
        if isinstance(item, Exception):
            out.append({"error": str(item)})
        else:
            out.append(item)
    return {"job_id": job_id, "outputs": out}


def _split_csv(value: str) -> list[str]:
    return [v.strip() for v in value.split(",") if v.strip()]


async def _job_cost_breakdown(job_id: str) -> dict[str, float]:
    async with aiosqlite.connect(DB_PATH) as db:
        cursor = await db.execute(
            """
            SELECT service, COALESCE(SUM(cost_usd), 0)
            FROM costs
            WHERE job_id = ?
            GROUP BY service
            """,
            (job_id,),
        )
        rows = await cursor.fetchall()
    by_service = {"exa": 0.0, "openai": 0.0, "claude": 0.0}
    for service, value in rows:
        by_service[str(service)] = float(value or 0.0)
    by_service["total"] = round(sum(by_service.values()), 6)
    return {k: round(v, 6) for k, v in by_service.items()}
