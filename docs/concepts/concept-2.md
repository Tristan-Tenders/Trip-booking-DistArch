# Database Transactions

## Category

A1 - Integrity and atomicity

## Problem

The flight and hotel services update inventory and create bookings using multiple database operations. In the baseline application, a failure between these operations can leave the database in a partially updated state.

## Invariant or guarantee

Inventory updates and booking creation are atomic. Either all changes succeed, or all changes are rolled back.

## Modified files

* `flight_service/main.py`
* `hotel_service/main.py`

## Behavior before

A forced failure after decrementing inventory could leave the system in an inconsistent state.

Example:

1. Seats available = 1
2. Seats decremented to 0
3. Failure occurs
4. No booking exists
5. Seats remain at 0

The inventory no longer matches the actual bookings.

## Behavior after

The booking operation runs inside a database transaction.

If a failure occurs after inventory is decremented, PostgreSQL rolls back the transaction.

Example:

1. Seats available = 1
2. Seats decremented
3. Failure occurs
4. Transaction rolls back
5. Seats remain at 1
6. No booking exists

The database remains consistent.

## How to test

Run a booking request with `fail_after_decrement=true`.

Verify:

* No booking is created.
* Inventory remains unchanged after the request fails.

This can be tested through the flight and hotel booking endpoints.

## Limitation

Transactions only protect data inside a single service database. They do not guarantee consistency across multiple services participating in a trip booking workflow.
