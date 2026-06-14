# Concept: Pessimistic Locking
**Category:** A2

## Problem
In the baseline, book_flight and reserve_hotel read availability, check it, then update — three separate steps with no protection. Under concurrent load, multiple requests pass the check before any update is visible. Result: seats_available goes negative.

## Invariant or guarantee
seats_available >= 0 at all times, even under concurrent requests.
rooms_available >= 0 at all times, even under concurrent requests.

## Modified files
- flight_service/main.py
- hotel_service/main.py

## Behavior before
Running demo_overbooking.py with 20 concurrent requests against FL-ONE-SEAT (1 seat) produces multiple successful bookings and seats_available < 0.

## Behavior after
Only one request acquires the row lock and succeeds. All others wait, then see 0 seats and receive 409. seats_available never drops below 0.

## How to test
docker compose run --rm tools python scripts/demo_overbooking.py

Before fix: multiple successes, negative seats.
After fix: exactly 1 success, 19 rejections, seats_available = 0.

## Limitation
Pessimistic locking serializes all concurrent requests for the same flight or hotel row. Under high concurrency this creates lock contention and reduces throughput. An alternative would be optimistic locking (version counter + retry on conflict), which allows more parallelism but requires retry logic at the application level.