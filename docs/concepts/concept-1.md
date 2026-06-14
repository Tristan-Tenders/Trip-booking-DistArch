# Idempotency key for client requests

## Category

C — Communication, consistency, or scaling

## Problem

`POST /trips` has no duplicate-request detection. If a client sends the same booking twice (network retry, double-click, timeout), the system creates two trips, two flight bookings, two hotel reservations, and two payments. Each request is treated as a new one.

## Invariant or guarantee

Two requests with the same `idempotency_key` produce one trip. The second request returns the same response as the first with no new bookings or charges.

## Modified files

- `trip_service/schemas.py` — added optional `idempotency_key` field to `CreateTripRequest`
- `trip_service/db.py` — added `idempotency_key` column (UNIQUE, nullable) to `trips`; added `get_trip_by_idempotency_key()`; updated `create_trip()` to store the key
- `trip_service/main.py` — checks for an existing trip by key before proceeding; handles concurrent-insert race via `UniqueViolationError`

## Behavior before

Two identical `POST /trips` calls both succeeded and created separate trips, with all downstream side effects happening twice.

## Behavior after

If the key already exists in the database, the endpoint returns the stored trip without calling any downstream service. If two requests with the same key arrive at the same time, the one that loses the insert race catches `UniqueViolationError` and returns the other's trip.

Requests without a key work the same as before.

## How to test

```bash
# shows both behaviors side by side
docker compose run --rm tools python scripts/demo_duplicate_request.py

# automated tests
docker compose run --rm tools pytest tests/test_idempotency.py -v
```

## Limitation

- If the first request fails (e.g. payment declined), the trip is stored as FAILED. A retry with the same key replays the original 502 response — it does not reattempt the booking. The client needs a new key to retry.
- The key has no expiry and no authentication — anyone who knows a key can reuse it.
- Keys are scoped to the `trips` table only, not across services.
