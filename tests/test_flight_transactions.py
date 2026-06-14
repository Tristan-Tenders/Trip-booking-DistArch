import os

import httpx

FLIGHT_URL = os.getenv("FLIGHT_URL", "http://localhost:8001")


def _reset():
    with httpx.Client(timeout=10) as client:
        client.post(f"{FLIGHT_URL}/admin/reset").raise_for_status()


def test_book_flight_rolls_back_on_forced_failure():
    _reset()
    with httpx.Client(timeout=10) as client:
        before = client.get(f"{FLIGHT_URL}/flights/FL-ONE-SEAT").json()

        response = client.post(
            f"{FLIGHT_URL}/flights/FL-ONE-SEAT/bookings",
            json={
                "trip_id": "11111111-1111-1111-1111-111111111111",
                "traveler_name": "Rollback Test",
                "seats": 1,
                "fail_after_decrement": True,
            },
        )

        after = client.get(f"{FLIGHT_URL}/flights/FL-ONE-SEAT").json()
        state = client.get(f"{FLIGHT_URL}/debug/state").json()

    assert response.status_code == 500
    assert after["seats_available"] == before["seats_available"]
    assert state["flight_bookings"] == []
