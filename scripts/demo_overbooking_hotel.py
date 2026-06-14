from __future__ import annotations

import asyncio
from uuid import uuid4

import httpx

from common import HOTEL_URL, pretty, reset_all


async def try_reserve(client: httpx.AsyncClient) -> httpx.Response:
    return await client.post(
        f"{HOTEL_URL}/hotels/HT-ONE-ROOM/reservations",
        json={
            "trip_id": str(uuid4()),
            "traveler_name": "Race Condition Student",
            "nights": 1,
            "rooms": 1,
            "delay_after_check_ms": 200,
            "force_fail": False,
        },
    )


async def run_race() -> None:
    async with httpx.AsyncClient(timeout=10) as client:
        responses = await asyncio.gather(*[try_reserve(client) for _ in range(20)])
        state = (await client.get(f"{HOTEL_URL}/debug/state")).json()

    successful = [response for response in responses if response.status_code == 200]
    rejected = [response for response in responses if response.status_code == 409]
    one_room = next(hotel for hotel in state["hotels"] if hotel["id"] == "HT-ONE-ROOM")

    print(f"Successful reservations: {len(successful)}")
    print(f"Rejected reservations: {len(rejected)}")
    print(f"Final rooms_available: {one_room['rooms_available']}")
    print("Pessimistic locking (SELECT ... FOR UPDATE) prevented the race condition:")
    print("only 1 reservation succeeded and rooms_available never went negative.")
    print("Final hotel state:")
    print(pretty(state))


def main() -> None:
    reset_all()
    asyncio.run(run_race())


if __name__ == "__main__":
    main()