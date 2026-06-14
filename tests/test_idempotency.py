from __future__ import annotations

import os
import time

import httpx

TRIP_URL = os.getenv("TRIP_URL", "http://localhost:8000")
FLIGHT_URL = os.getenv("FLIGHT_URL", "http://localhost:8001")
HOTEL_URL = os.getenv("HOTEL_URL", "http://localhost:8002")
PAYMENT_URL = os.getenv("PAYMENT_URL", "http://localhost:8003")
NOTIFICATION_URL = os.getenv("NOTIFICATION_URL", "http://localhost:8004")
SERVICE_URLS = [TRIP_URL, FLIGHT_URL, HOTEL_URL, PAYMENT_URL, NOTIFICATION_URL]


def reset_all() -> None:
    import asyncio
    from shared.rabbitmq import purge_notification_queue
    asyncio.run(purge_notification_queue())
    with httpx.Client(timeout=10) as client:
        for base_url in SERVICE_URLS:
            client.post(f"{base_url}/admin/reset").raise_for_status()


def trip_payload(idempotency_key: str | None = None, **simulate):
    payload = {
        "user_id": "user-1",
        "traveler_name": "Ada Lovelace",
        "flight_id": "FL-MANY-SEATS",
        "hotel_id": "HT-MANY-ROOMS",
        "nights": 2,
        "simulate": simulate,
    }
    if idempotency_key is not None:
        payload["idempotency_key"] = idempotency_key
    return payload


def test_same_idempotency_key_returns_same_trip() -> None:
    reset_all()
    with httpx.Client(timeout=15) as client:
        first = client.post(f"{TRIP_URL}/trips", json=trip_payload(idempotency_key="key-001"))
        second = client.post(f"{TRIP_URL}/trips", json=trip_payload(idempotency_key="key-001"))

    assert first.status_code == 200
    assert second.status_code == 200
    assert first.json()["id"] == second.json()["id"]


def test_idempotency_key_prevents_duplicate_side_effects() -> None:
    reset_all()
    with httpx.Client(timeout=15) as client:
        client.post(f"{TRIP_URL}/trips", json=trip_payload(idempotency_key="key-002"))
        client.post(f"{TRIP_URL}/trips", json=trip_payload(idempotency_key="key-002"))

        trips = client.get(f"{TRIP_URL}/trips").json()
        flight_state = client.get(f"{FLIGHT_URL}/debug/state").json()
        hotel_state = client.get(f"{HOTEL_URL}/debug/state").json()
        payment_state = client.get(f"{PAYMENT_URL}/debug/state").json()

    assert len(trips) == 1
    assert len(flight_state["flight_bookings"]) == 1
    assert len(hotel_state["hotel_reservations"]) == 1
    assert len(payment_state["payment_authorizations"]) == 1


def test_different_keys_create_different_trips() -> None:
    reset_all()
    with httpx.Client(timeout=15) as client:
        first = client.post(f"{TRIP_URL}/trips", json=trip_payload(idempotency_key="key-003"))
        second = client.post(f"{TRIP_URL}/trips", json=trip_payload(idempotency_key="key-004"))

    assert first.status_code == 200
    assert second.status_code == 200
    assert first.json()["id"] != second.json()["id"]


def test_no_key_still_creates_duplicate_trips() -> None:
    """Requests without an idempotency key retain baseline behavior."""
    reset_all()
    with httpx.Client(timeout=15) as client:
        first = client.post(f"{TRIP_URL}/trips", json=trip_payload())
        second = client.post(f"{TRIP_URL}/trips", json=trip_payload())

    assert first.status_code == 200
    assert second.status_code == 200
    assert first.json()["id"] != second.json()["id"]


def test_idempotency_key_on_failed_trip_returns_failure() -> None:
    """A repeated request for a failed trip replays the original 502, not a new attempt."""
    reset_all()
    with httpx.Client(timeout=15) as client:
        first = client.post(
            f"{TRIP_URL}/trips",
            json=trip_payload(idempotency_key="key-fail-001", payment_force_decline=True),
        )
        second = client.post(
            f"{TRIP_URL}/trips",
            json=trip_payload(idempotency_key="key-fail-001", payment_force_decline=True),
        )

    assert first.status_code == 502
    assert second.status_code == 502
    assert first.json()["detail"]["trip_id"] == second.json()["detail"]["trip_id"]
