# Pessimistic Locking

## Category

A2 - Concurrency control

## Problem

`book_flight` and `reserve_hotel` each run inside a database transaction (see
concept-2.md), but the transaction alone does not stop two concurrent
requests from both reading the same `seats_available` / `rooms_available`
value before either has written its update. Under PostgreSQL's default
isolation level, a plain `SELECT` does not block concurrent transactions from
reading the same row. Multiple requests can therefore pass the availability
check at the same time and all decrement the inventory, producing a negative
value.

## Invariant or guarantee

`seats_available >= 0` and `rooms_available >= 0` hold even when many
requests for the same flight or hotel arrive concurrently. At most one
request can book the last remaining seat or room.

## Modified files

- `flight_service/main.py` - `book_flight`: added `FOR UPDATE` to the flight
  row lookup.
- `hotel_service/main.py` - `reserve_hotel`: added `FOR UPDATE` to the hotel
  row lookup.
- `scripts/demo_overbooking.py` - updated output message to reflect the fixed
  behavior.
- `scripts/demo_overbooking_hotel.py` - new script, same scenario for hotel
  reservations.

## Behavior before

Sending 20 concurrent booking requests for `FL-ONE-SEAT` (1 seat available)
resulted in multiple requests passing the availability check before any
decrement was visible, leaving `seats_available` negative.

## Behavior after

`SELECT ... FOR UPDATE` locks the flight/hotel row for the duration of the
transaction. The first request to acquire the lock sees `seats_available = 1`,
decrements it to 0, and commits. Every other request must wait for the lock;
once acquired, they see `seats_available = 0` and return `409 Not enough
seats available`. `seats_available` never drops below 0.

## How to test

```bash
docker compose run --rm tools python scripts/demo_overbooking.py
docker compose run --rm tools python scripts/demo_overbooking_hotel.py
```

Expected output for both: 1 successful booking, 19 rejected, final
availability = 0.

## Limitation

Pessimistic locking serializes all concurrent requests for the same flight or
hotel row, even when they would not actually conflict (e.g. two requests each
booking 1 of 10 available seats still queue behind each other). Under high
contention this increases request latency and can lead to lock-wait timeouts.
An alternative would be optimistic locking (a `version` column checked on
update, with the client retrying on conflict), which allows more parallelism
at the cost of requiring retry logic in the caller.