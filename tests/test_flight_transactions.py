import pytest
import asyncpg


@pytest.mark.asyncio
async def test_flight_booking_transaction_rollback(flight_db_pool):
    async with flight_db_pool.acquire() as conn:

        # get initial state
        before = await conn.fetchrow("""
            SELECT seats_available
            FROM flights
            WHERE id = 'FL-MANY-SEATS'
        """)

        # attempt booking that forces failure after decrement
        try:
            async with conn.transaction():
                await conn.fetchrow("""
                    UPDATE flights
                    SET seats_available = seats_available - 1
                    WHERE id = 'FL-MANY-SEATS'
                """)

                # simulate failure (like your fail_after_decrement logic)
                raise Exception("forced failure")

        except Exception:
            pass

        # check state still valid (no negative or inconsistent change)
        after = await conn.fetchrow("""
            SELECT seats_available
            FROM flights
            WHERE id = 'FL-MANY-SEATS'
        """)

        assert after["seats_available"] == before["seats_available"]