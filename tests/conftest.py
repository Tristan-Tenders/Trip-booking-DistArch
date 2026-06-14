from __future__ import annotations

import os
from pathlib import Path
import sys

import asyncpg
import pytest

ROOT_DIR = Path(__file__).resolve().parents[1]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

FLIGHT_DATABASE_URL = os.getenv(
    "FLIGHT_DATABASE_URL", "postgresql://postgres:postgres@postgres:5432/flight_db"
)


@pytest.fixture
async def flight_db_pool():
    pool = await asyncpg.create_pool(FLIGHT_DATABASE_URL)
    yield pool
    await pool.close()
