import pytest
import asyncpg


@pytest.mark.asyncio
async def test_flight_seats_constraint(flight_db_pool):
    async with flight_db_pool.acquire() as conn:

        with pytest.raises(asyncpg.CheckViolationError):
            await conn.execute("""
                UPDATE flights
                SET seats_available = -10
                WHERE id = 'FL-MANY-SEATS'
            """)