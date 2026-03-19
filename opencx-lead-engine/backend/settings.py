from __future__ import annotations

import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
IS_VERCEL = os.getenv("VERCEL") == "1"

# Use /tmp in serverless runtimes and backend root locally.
DEFAULT_DATA_DIR = Path("/tmp/opencx-lead-engine") if IS_VERCEL else BASE_DIR
DATA_DIR = Path(os.getenv("OPENCX_DATA_DIR", str(DEFAULT_DATA_DIR)))
EXPORT_DIR = DATA_DIR / "exports"
DB_PATH = DATA_DIR / "jobs.db"
EXA_CACHE_PATH = DATA_DIR / "exa_raw_cache.json"

DATA_DIR.mkdir(parents=True, exist_ok=True)
EXPORT_DIR.mkdir(parents=True, exist_ok=True)


def cors_origins() -> list[str]:
    configured = os.getenv("CORS_ORIGINS", "")
    if configured.strip():
        return [part.strip() for part in configured.split(",") if part.strip()]
    return ["http://localhost:5173", "http://127.0.0.1:5173"]
