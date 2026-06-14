# Database Constraints

## Category

A1 - Integrity and atomicity

## Problem

The baseline application relies entirely on application code to keep inventory values valid. A bug or incorrect update could create negative seat or room counts.

## Invariant or guarantee

The database enforces:

* `seats_available >= 0`
* `rooms_available >= 0`

Negative inventory values cannot be stored.

## Modified files

* `flight_service/db.py`
* `hotel_service/db.py`

## Behavior before

An incorrect update could create invalid inventory values.

Example:

* Seats available = 0
* Update seats_available to -1
* Database accepts the change

The system contains invalid state.

## Behavior after

CHECK constraints are enforced by PostgreSQL.

Examples:

* `CHECK (seats_available >= 0)`
* `CHECK (rooms_available >= 0)`

Any update that would produce a negative value is rejected.

## How to test

Attempt an update such as:

UPDATE flights
SET seats_available = -1
WHERE id = 'FL-ONE-SEAT';

PostgreSQL should reject the update with a constraint violation.

The same applies to hotel inventory.

## Limitation

Constraints prevent invalid values from being stored, but they do not prevent concurrent requests from reading the same inventory value. Concurrency control is handled separately through pessimistic locking.
