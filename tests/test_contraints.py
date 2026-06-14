import os

import asyncpg
import pytest

FLIGHT_DATABASE_URL = os.getenv(
    "FLIGHT_DATABASE_URL", "postgresql://postgres:postgres@postgres:5432/flight_db"
)


@pytest.mark.asyncio
async def test_flight_seats_constraint():
    conn = await asyncpg.connect(FLIGHT_DATABASE_URL)
    try:
        with pytest.raises(asyncpg.CheckViolationError):
            await conn.execute("""
                UPDATE flights
                SET seats_available = -10
                WHERE id = 'FL-MANY-SEATS'
            """)
    finally:
        await conn.close()
