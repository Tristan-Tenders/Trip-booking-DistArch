# Saga with compensation (durable state machine)

## Category

B — Distributed workflow or messaging

## Problem

Booking a trip spans three remote services (flight, hotel, payment). In the baseline
application, if payment fails after the flight and hotel are already reserved, those
reservations stay CONFIRMED forever. The trip is left in a failed state while remote
resources remain held, and there is no record of the recovery attempt.

## Invariant or guarantee

A trip never ends in a state where it is not CONFIRMED but its flight/hotel resources are
still held. Either the trip reaches CONFIRMED, or every successfully-reserved resource is
cancelled and the trip reaches a terminal COMPENSATED state. The trip row durably records
the intermediate states (PENDING → COMPENSATING → COMPENSATED, or COMPENSATION_FAILED) so
the outcome is auditable, not just inferred.

## Modified files

- `trip_service/main.py` — `create_trip`: wraps the remote-call sequence; on any failure
  transitions the trip to COMPENSATING, cancels the flight booking and hotel reservation
  via the flight/hotel services, then sets COMPENSATED (or COMPENSATION_FAILED if a
  cancel call itself fails).
- `trip_service/db.py` — `update_trip` persists each state transition so intermediate and
  terminal states are durable in the `trips` table.
- `trip_service/clients.py` — `cancel_flight_booking`, `cancel_hotel_reservation`: the
  compensating actions invoked during rollback.

## Behavior before

A payment decline after flight + hotel success left the flight booking and hotel
reservation CONFIRMED, with the trip stuck in a failed state and no compensation.

## Behavior after

On payment failure the trip moves to COMPENSATING, the flight booking and hotel
reservation are cancelled (status CANCELLED in their own services), and the trip becomes
COMPENSATED. The endpoint returns 502 with the trip_id and final compensation status. If a
cancellation call fails, the trip is recorded as COMPENSATION_FAILED rather than silently
losing the error.

## How to test

```bash
docker compose run --rm tools python scripts/demo_partial_failure.py
docker compose run --rm tools pytest tests/test_intentional_flaws.py::test_payment_failure_triggers_compensation -v
```

Expected: trip status COMPENSATED, flight booking CANCELLED, hotel reservation CANCELLED,
payment authorization DECLINED.

## Limitation

Compensation runs in-line inside the request handler. If the trip-service process crashes
mid-compensation, there is no background recovery to resume it — the trip stays in
COMPENSATING. Cancellations are also not idempotent in the flight/hotel services (calling a
cancel twice would increment inventory twice), so the saga relies on each compensating
action running exactly once. A production version would persist the saga log to a durable
queue and make compensating actions idempotent.
