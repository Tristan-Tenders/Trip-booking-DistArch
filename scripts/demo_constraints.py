import asyncio
import os

import asyncpg

FLIGHT_DATABASE_URL = os.getenv(
    "FLIGHT_DATABASE_URL", "postgresql://postgres:postgres@postgres:5432/flight_db"
)
HOTEL_DATABASE_URL = os.getenv(
    "HOTEL_DATABASE_URL", "postgresql://postgres:postgres@postgres:5432/hotel_db"
)


async def demo() -> None:
    print("=== DATABASE CONSTRAINT DEMO ===")
    print("Bypasses the application-level availability check and attempts a direct")
    print("negative-value UPDATE, demonstrating the CHECK constraint as last line of defense.\n")

    conn = await asyncpg.connect(FLIGHT_DATABASE_URL)
    try:
        await conn.execute(
            "UPDATE flights SET seats_available = -1 WHERE id = 'FL-ONE-SEAT'"
        )
        print("FAIL: flight seats_available = -1 was accepted (constraint missing)")
    except asyncpg.CheckViolationError:
        print("PASS: flight CHECK constraint rejected seats_available = -1")
    finally:
        await conn.close()

    conn = await asyncpg.connect(HOTEL_DATABASE_URL)
    try:
        await conn.execute(
            "UPDATE hotels SET rooms_available = -1 WHERE id = 'HT-ONE-ROOM'"
        )
        print("FAIL: hotel rooms_available = -1 was accepted (constraint missing)")
    except asyncpg.CheckViolationError:
        print("PASS: hotel CHECK constraint rejected rooms_available = -1")
    finally:
        await conn.close()


if __name__ == "__main__":
    asyncio.run(demo())
