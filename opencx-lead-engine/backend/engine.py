from __future__ import annotations

import asyncio
import json
from datetime import datetime
from typing import Any

import aiosqlite

from costs import CostTracker
from db import (
    DB_PATH,
    append_log,
    is_cancel_requested,
    replace_results,
    update_job_status,
    update_job_totals,
)
from enrichers.base import get_exa_client, load_plugins as load_enricher_plugins
from lists.base import load_plugins as load_list_plugins
from models.base import load_plugins as load_model_plugins
from outputs.base import load_plugins as load_output_plugins
from settings import EXA_CACHE_PATH


class JobCancelled(Exception):
    pass


async def _check_cancel(job_id: str) -> None:
    if await is_cancel_requested(job_id):
        await append_log(job_id, "Cancellation requested. Stopping job.", "yellow")
        await update_job_status(job_id, "cancelled")
        raise JobCancelled("Job cancelled")


def _dedupe_by_domain(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    bucket: dict[str, dict[str, Any]] = {}
    for row in rows:
        domain = row.get("domain")
        if not domain:
            continue
        if domain not in bucket:
            bucket[domain] = {
                "domain": domain,
                "company_name_hint": row.get("title") or domain,
                "primary_url": row.get("url"),
                "sources": [row.get("source")],
                "highlights": row.get("highlights", []),
                "summaries": [row.get("summary", "")],
                "raw_items": [row.get("raw", {})],
            }
        else:
            bucket[domain]["sources"].append(row.get("source"))
            bucket[domain]["highlights"].extend(row.get("highlights", []))
            if row.get("summary"):
                bucket[domain]["summaries"].append(row.get("summary"))
            bucket[domain]["raw_items"].append(row.get("raw", {}))

    deduped = []
    for _, v in bucket.items():
        deduped.append(
            {
                **v,
                "sources": sorted({s for s in v["sources"] if s}),
                "highlights": list(dict.fromkeys([h for h in v["highlights"] if h]))[:25],
                "summaries": [s for s in v["summaries"] if s][:10],
            }
        )
    return deduped


def _tier_for_score(score: int) -> int:
    if score >= 75:
        return 1
    if score >= 60:
        return 2
    return 3


def _normalize_qualified(company: dict[str, Any], qualified: dict[str, Any]) -> dict[str, Any]:
    fit_score = int(qualified.get("fit_score", 0) or 0)
    row = {
        "qualifies": bool(qualified.get("qualifies", fit_score > 0)),
        "fit_score": fit_score,
        "icp_tier": int(qualified.get("icp_tier", _tier_for_score(fit_score))),
        "company_name": qualified.get("company_name") or company.get("company_name_hint") or company["domain"],
        "domain": qualified.get("domain") or company["domain"],
        "country": qualified.get("country") or "Unknown",
        "city": qualified.get("city"),
        "industry": qualified.get("industry") or "Unknown",
        "estimated_total_employees": qualified.get("estimated_total_employees"),
        "estimated_support_headcount": qualified.get("estimated_support_headcount"),
        "support_signals": qualified.get("support_signals") or [],
        "risk_flags": qualified.get("risk_flags") or [],
        "fit_reason": qualified.get("fit_reason") or "",
        "suggested_angle": qualified.get("suggested_angle") or "",
        "sources": company.get("sources", []),
        "highlights": company.get("highlights", []),
        "primary_url": company.get("primary_url"),
    }
    return row


async def _cost_totals_for_job(job_id: str) -> dict[str, float]:
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
    out = {"exa": 0.0, "openai": 0.0, "claude": 0.0}
    for service, total in rows:
        out[str(service)] = float(total or 0.0)
    out["total"] = out["exa"] + out["openai"] + out["claude"]
    return out


async def run_pipeline(job_id: str, config: dict[str, Any]) -> None:
    tracker = CostTracker(job_id)

    try:
        enricher_plugins = load_enricher_plugins()
        model_plugins = load_model_plugins()
        list_plugins = load_list_plugins()
        output_plugins = load_output_plugins()

        await _check_cancel(job_id)
        await update_job_status(job_id, "phase_1_planning")
        await append_log(job_id, "Phase 1: planning started", "gray", "phase_1")

        list_type_key = config.get("list_type", "high_volume")
        list_type = list_plugins[list_type_key]
        regions = config.get("regions", ["NL", "BE"])
        anchors = config.get("anchor_urls") or list_type.get_anchors(regions)
        planner_model = model_plugins[config.get("planner_model", "claude-haiku-4-5")]
        plan = await planner_model.plan(
            prompt=config.get("prompt", ""),
            list_type=list_type_key,
            regions=regions,
            anchors=anchors,
            cost_tracker=tracker,
        )
        await append_log(job_id, "Planning complete", "gray", "phase_1")

        await _check_cancel(job_id)
        await update_job_status(job_id, "phase_2_discovery")
        await append_log(job_id, "Phase 2: enrichers running in parallel", "gray", "phase_2")

        exa = get_exa_client()
        selected_enrichers = set(config.get("enrichers", ["exa_neural", "exa_similar", "exa_keyword"]))
        neural_queries = plan.get("neural_queries", [])
        keyword_queries = plan.get("keyword_queries", [])
        similar_urls = plan.get("find_similar_urls", anchors)
        directory_urls = plan.get("directory_urls", [])
        livecrawl_queries = plan.get("livecrawl_queries", [])

        all_tasks: list[asyncio.Task] = []
        if "exa_neural" in selected_enrichers and "exa_neural" in enricher_plugins:
            all_tasks += [
                asyncio.create_task(enricher_plugins["exa_neural"].run(exa, q, config, tracker))
                for q in neural_queries
            ]
        if "exa_similar" in selected_enrichers and "exa_similar" in enricher_plugins:
            all_tasks += [
                asyncio.create_task(enricher_plugins["exa_similar"].run(exa, u, config, tracker))
                for u in similar_urls
            ]
        if "exa_keyword" in selected_enrichers and "exa_keyword" in enricher_plugins:
            all_tasks += [
                asyncio.create_task(enricher_plugins["exa_keyword"].run(exa, q, config, tracker))
                for q in keyword_queries
            ]
        if "exa_contents" in selected_enrichers and "exa_contents" in enricher_plugins:
            all_tasks += [
                asyncio.create_task(enricher_plugins["exa_contents"].run(exa, u, config, tracker))
                for u in directory_urls
            ]
        if "exa_livecrawl" in selected_enrichers and "exa_livecrawl" in enricher_plugins:
            all_tasks += [
                asyncio.create_task(enricher_plugins["exa_livecrawl"].run(exa, q, config, tracker))
                for q in livecrawl_queries
            ]

        phase2_flat: list[dict[str, Any]] = []
        if all_tasks:
            results = await asyncio.gather(*all_tasks, return_exceptions=True)
            for result in results:
                if isinstance(result, Exception):
                    await append_log(job_id, f"Enricher error: {result}", "red", "phase_2")
                else:
                    phase2_flat.extend(result)

        deduped_phase2 = _dedupe_by_domain(phase2_flat)
        await append_log(
            job_id,
            f"Phase 2 complete: {len(phase2_flat)} raw rows -> {len(deduped_phase2)} unique domains",
            "gray",
            "phase_2",
        )

        EXA_CACHE_PATH.write_text(
            json.dumps(
                {
                    "job_id": job_id,
                    "created_at": datetime.utcnow().isoformat(),
                    "plan": plan,
                    "raw_results": phase2_flat,
                    "deduped": deduped_phase2,
                },
                ensure_ascii=True,
                indent=2,
            ),
            encoding="utf-8",
        )

        await _check_cancel(job_id)
        await update_job_status(job_id, "phase_3_deep_enrichment")
        await append_log(job_id, "Phase 3: deep enrichment started", "gray", "phase_3")

        phase3_flat: list[dict[str, Any]] = []
        if "exa_keyword" in enricher_plugins:
            deep_tasks = []
            for row in deduped_phase2:
                q = f"site:{row['domain']} customer support careers"
                deep_tasks.append(asyncio.create_task(enricher_plugins["exa_keyword"].run(exa, q, config, tracker)))
            if deep_tasks:
                deep_results = await asyncio.gather(*deep_tasks, return_exceptions=True)
                for result in deep_results:
                    if isinstance(result, Exception):
                        await append_log(job_id, f"Deep enrich error: {result}", "red", "phase_3")
                    else:
                        phase3_flat.extend(result)

        merged = _dedupe_by_domain(phase2_flat + phase3_flat)
        await append_log(job_id, f"Phase 3 complete: {len(merged)} enriched domains", "gray", "phase_3")

        await _check_cancel(job_id)
        await update_job_status(job_id, "phase_4_qualification")
        await append_log(job_id, "Phase 4: qualification started", "gray", "phase_4")

        qualifier_model = model_plugins[config.get("qualifier_model", "gpt-4o")]
        system_prompt = list_type.get_system_prompt()
        gpt_sem = asyncio.Semaphore(15)

        async def _qualify_one(company: dict[str, Any]) -> dict[str, Any] | None:
            async with gpt_sem:
                if await is_cancel_requested(job_id):
                    return None
                payload = {
                    "domain": company["domain"],
                    "company_name_hint": company.get("company_name_hint"),
                    "highlights": company.get("highlights", []),
                    "sources": company.get("sources", []),
                    "summary": " ".join(company.get("summaries", [])[:3]),
                    "primary_url": company.get("primary_url"),
                }
                qualified = await qualifier_model.qualify(payload, system_prompt, tracker)
                row = _normalize_qualified(company, qualified)
                if row["fit_score"] <= 0:
                    return None
                level = "green" if row["fit_score"] >= 60 else "yellow"
                await append_log(
                    job_id,
                    f"Qualified {row['company_name']} ({row['fit_score']})",
                    level,
                    "phase_4",
                )
                return row

        qualified_rows = await asyncio.gather(*[_qualify_one(c) for c in merged], return_exceptions=True)
        final_rows: list[dict[str, Any]] = []
        for item in qualified_rows:
            if isinstance(item, Exception):
                await append_log(job_id, f"Qualification error: {item}", "red", "phase_4")
            elif isinstance(item, dict):
                final_rows.append(item)

        final_rows = sorted(final_rows, key=lambda x: x.get("fit_score", 0), reverse=True)
        await replace_results(job_id, final_rows)
        await append_log(job_id, f"Phase 4 complete: {len(final_rows)} qualified companies", "gray", "phase_4")

        await _check_cancel(job_id)
        await update_job_status(job_id, "phase_5_outputs")
        await append_log(job_id, "Phase 5: outputs started", "gray", "phase_5")

        output_keys = config.get("outputs") or ["csv_writer"]
        output_tasks = []
        for key in output_keys:
            plugin = output_plugins.get(key)
            if plugin:
                output_tasks.append(asyncio.create_task(plugin.run(job_id, final_rows, config)))
        output_results = await asyncio.gather(*output_tasks, return_exceptions=True)
        for out_result in output_results:
            if isinstance(out_result, Exception):
                await append_log(job_id, f"Output error: {out_result}", "red", "phase_5")
            else:
                await append_log(job_id, f"Output complete: {out_result}", "blue", "phase_5")

        await update_job_status(job_id, "phase_6_finalize")
        await append_log(job_id, "Phase 6: finalizing run", "gray", "phase_6")

        await tracker.flush()
        totals = await _cost_totals_for_job(job_id)
        await update_job_totals(job_id, round(totals["total"], 6), len(final_rows))
        await update_job_status(job_id, "completed")
        await append_log(job_id, "Job completed", "green", "phase_6")

    except JobCancelled:
        return
    except Exception as exc:
        await append_log(job_id, f"Job failed: {exc}", "red")
        await update_job_status(job_id, "failed")
