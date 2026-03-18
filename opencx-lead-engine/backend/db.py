from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any

import aiosqlite

DB_PATH = Path(__file__).resolve().parent / "jobs.db"


async def create_tables() -> None:
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            """
            CREATE TABLE IF NOT EXISTS jobs (
                id TEXT PRIMARY KEY,
                status TEXT,
                config_json TEXT,
                prompt TEXT,
                list_type TEXT,
                regions TEXT,
                created_at TEXT,
                completed_at TEXT,
                total_cost_usd REAL,
                companies_found INTEGER
            )
            """
        )
        await db.execute(
            """
            CREATE TABLE IF NOT EXISTS results (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                job_id TEXT,
                company_json TEXT,
                fit_score INTEGER,
                icp_tier INTEGER,
                created_at TEXT
            )
            """
        )
        await db.execute(
            """
            CREATE TABLE IF NOT EXISTS costs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                job_id TEXT,
                service TEXT,
                call_type TEXT,
                model TEXT,
                tokens_in INTEGER,
                tokens_out INTEGER,
                cost_usd REAL,
                ts TEXT
            )
            """
        )
        await db.execute(
            """
            CREATE TABLE IF NOT EXISTS logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                job_id TEXT,
                level TEXT,
                message TEXT,
                phase TEXT,
                ts TEXT
            )
            """
        )
        await db.commit()


async def create_job(job_id: str, config: dict[str, Any]) -> None:
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            """
            INSERT INTO jobs (
                id, status, config_json, prompt, list_type, regions,
                created_at, completed_at, total_cost_usd, companies_found
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                job_id,
                "queued",
                json.dumps(config),
                config.get("prompt", ""),
                config.get("list_type", ""),
                json.dumps(config.get("regions", [])),
                datetime.utcnow().isoformat(),
                None,
                0.0,
                0,
            ),
        )
        await db.commit()


async def update_job_status(job_id: str, status: str) -> None:
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("UPDATE jobs SET status = ? WHERE id = ?", (status, job_id))
        if status in {"completed", "failed", "cancelled"}:
            await db.execute(
                "UPDATE jobs SET completed_at = ? WHERE id = ?",
                (datetime.utcnow().isoformat(), job_id),
            )
        await db.commit()


async def mark_cancel_requested(job_id: str) -> None:
    await update_job_status(job_id, "cancel_requested")


async def is_cancel_requested(job_id: str) -> bool:
    async with aiosqlite.connect(DB_PATH) as db:
        cursor = await db.execute("SELECT status FROM jobs WHERE id = ?", (job_id,))
        row = await cursor.fetchone()
    return bool(row and row[0] == "cancel_requested")


async def append_log(job_id: str, message: str, level: str = "info", phase: str = "") -> None:
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            "INSERT INTO logs (job_id, level, message, phase, ts) VALUES (?, ?, ?, ?, ?)",
            (job_id, level, message, phase, datetime.utcnow().isoformat()),
        )
        await db.commit()


async def replace_results(job_id: str, results: list[dict[str, Any]]) -> None:
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("DELETE FROM results WHERE job_id = ?", (job_id,))
        for company in results:
            await db.execute(
                """
                INSERT INTO results (job_id, company_json, fit_score, icp_tier, created_at)
                VALUES (?, ?, ?, ?, ?)
                """,
                (
                    job_id,
                    json.dumps(company),
                    int(company.get("fit_score", 0)),
                    int(company.get("icp_tier", 3)),
                    datetime.utcnow().isoformat(),
                ),
            )
        await db.commit()


async def update_job_totals(job_id: str, total_cost_usd: float, companies_found: int) -> None:
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            """
            UPDATE jobs
            SET total_cost_usd = ?, companies_found = ?
            WHERE id = ?
            """,
            (total_cost_usd, companies_found, job_id),
        )
        await db.commit()


async def get_job(job_id: str) -> dict[str, Any] | None:
    async with aiosqlite.connect(DB_PATH) as db:
        cursor = await db.execute(
            """
            SELECT id, status, config_json, prompt, list_type, regions,
                   created_at, completed_at, total_cost_usd, companies_found
            FROM jobs WHERE id = ?
            """,
            (job_id,),
        )
        row = await cursor.fetchone()
    if not row:
        return None
    return {
        "id": row[0],
        "status": row[1],
        "config_json": json.loads(row[2]) if row[2] else {},
        "prompt": row[3],
        "list_type": row[4],
        "regions": json.loads(row[5]) if row[5] else [],
        "created_at": row[6],
        "completed_at": row[7],
        "total_cost_usd": row[8] or 0.0,
        "companies_found": row[9] or 0,
    }


async def get_job_logs(job_id: str, limit: int = 200) -> list[dict[str, Any]]:
    async with aiosqlite.connect(DB_PATH) as db:
        cursor = await db.execute(
            """
            SELECT level, message, phase, ts
            FROM logs
            WHERE job_id = ?
            ORDER BY id ASC
            LIMIT ?
            """,
            (job_id, limit),
        )
        rows = await cursor.fetchall()
    return [{"level": r[0], "message": r[1], "phase": r[2], "ts": r[3]} for r in rows]


async def get_results(job_id: str) -> list[dict[str, Any]]:
    async with aiosqlite.connect(DB_PATH) as db:
        cursor = await db.execute(
            "SELECT company_json FROM results WHERE job_id = ? ORDER BY fit_score DESC, id ASC",
            (job_id,),
        )
        rows = await cursor.fetchall()
    return [json.loads(r[0]) for r in rows]


async def get_cost_rows_for_job(job_id: str) -> list[dict[str, Any]]:
    async with aiosqlite.connect(DB_PATH) as db:
        cursor = await db.execute(
            """
            SELECT service, call_type, model, tokens_in, tokens_out, cost_usd, ts
            FROM costs
            WHERE job_id = ?
            ORDER BY id ASC
            """,
            (job_id,),
        )
        rows = await cursor.fetchall()
    return [
        {
            "service": r[0],
            "call_type": r[1],
            "model": r[2],
            "tokens_in": r[3],
            "tokens_out": r[4],
            "cost_usd": r[5],
            "ts": r[6],
        }
        for r in rows
    ]


async def get_cost_totals() -> dict[str, Any]:
    async with aiosqlite.connect(DB_PATH) as db:
        cursor = await db.execute(
            """
            SELECT service, COALESCE(SUM(cost_usd), 0)
            FROM costs
            GROUP BY service
            """
        )
        rows = await cursor.fetchall()

        job_cursor = await db.execute(
            "SELECT COUNT(*), COALESCE(SUM(total_cost_usd), 0), COALESCE(SUM(companies_found), 0) FROM jobs"
        )
        jobs_row = await job_cursor.fetchone()

    by_service = {"exa": 0.0, "openai": 0.0, "claude": 0.0}
    for service, total in rows:
        by_service[service] = float(total or 0.0)

    total_usd = round(sum(by_service.values()), 6)
    total_runs = int(jobs_row[0] or 0)
    total_cost_all_runs = float(jobs_row[1] or 0.0)
    total_companies = int(jobs_row[2] or 0)
    avg_cost_per_run = round(total_cost_all_runs / total_runs, 6) if total_runs else 0.0
    avg_cost_per_company = round(total_cost_all_runs / total_companies, 6) if total_companies else 0.0

    return {
        "total_usd": round(total_usd, 6),
        "by_service": {k: round(v, 6) for k, v in by_service.items()},
        "total_runs": total_runs,
        "avg_cost_per_run": avg_cost_per_run,
        "avg_cost_per_company": avg_cost_per_company,
    }


async def get_history(limit: int = 50) -> list[dict[str, Any]]:
    async with aiosqlite.connect(DB_PATH) as db:
        cursor = await db.execute(
            """
            SELECT id, prompt, status, created_at, completed_at,
                   total_cost_usd, companies_found
            FROM jobs
            ORDER BY created_at DESC
            LIMIT ?
            """,
            (limit,),
        )
        rows = await cursor.fetchall()

    return [
        {
            "job_id": r[0],
            "prompt": r[1],
            "status": r[2],
            "created_at": r[3],
            "completed_at": r[4],
            "total_cost_usd": float(r[5] or 0.0),
            "companies_found": int(r[6] or 0),
        }
        for r in rows
    ]
