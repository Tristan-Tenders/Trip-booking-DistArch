import os

import asyncpg
import pytest

FLIGHT_DATABASE_URL = os.getenv(
    "FLIGHT_DATABASE_URL", "postgresql://postgres:postgres@postgres:5432/flight_db"
)


@pytest.mark.asyncio
async def test_flight_booking_transaction_rollback():
    conn = await asyncpg.connect(FLIGHT_DATABASE_URL)
    try:
        before = await conn.fetchrow("""
            SELECT seats_available
            FROM flights
            WHERE id = 'FL-MANY-SEATS'
        """)

        try:
            async with conn.transaction():
                await conn.fetchrow("""
                    UPDATE flights
                    SET seats_available = seats_available - 1
                    WHERE id = 'FL-MANY-SEATS'
                """)

                raise Exception("forced failure")

        except Exception:
            pass

        after = await conn.fetchrow("""
            SELECT seats_available
            FROM flights
            WHERE id = 'FL-MANY-SEATS'
        """)

        assert after["seats_available"] == before["seats_available"]
    finally:
        await conn.close()
