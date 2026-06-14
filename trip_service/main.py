from __future__ import annotations

import logging
from contextlib import asynccontextmanager
from uuid import UUID

import asyncpg
from fastapi import FastAPI, HTTPException

from shared.logging import configure_logging
from trip_service import clients, db, events
from trip_service.pricing import calculate_amount_cents
from trip_service.schemas import CreateTripRequest

SERVICE_NAME = "trip-service"


@asynccontextmanager
async def lifespan(app: FastAPI):
    configure_logging(SERVICE_NAME)
    await db.connect_with_retry()
    await db.init_db()
    yield
    await db.close()


app = FastAPI(title="Trip Service", lifespan=lifespan)


@app.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok", "service": SERVICE_NAME}


@app.post("/admin/reset")
async def reset() -> dict[str, str]:
    await db.reset_db()
    return {"status": "ok"}


@app.get("/debug/state")
async def debug_state() -> dict:
    return await db.state()


@app.get("/trips")
async def list_trips() -> list[dict]:
    return (await db.state())["trips"]


@app.get("/trips/{trip_id}")
async def get_trip(trip_id: UUID) -> dict:
    trip = await db.get_trip(trip_id)
    if trip is None:
        raise HTTPException(status_code=404, detail="Trip not found")
    return trip


@app.post("/trips")
async def create_trip(request: CreateTripRequest) -> dict:
    if request.idempotency_key is not None:
        existing = await db.get_trip_by_idempotency_key(request.idempotency_key)
        if existing is not None:
            if existing["status"] not in ("CONFIRMED", "PENDING"):
                raise HTTPException(
                    status_code=502,
                    detail={"trip_id": str(existing["id"]), "error": existing["error_message"]},
                )
            return existing

    try:
        trip = await db.create_trip(
            user_id=request.user_id,
            traveler_name=request.traveler_name,
            flight_id=request.flight_id,
            hotel_id=request.hotel_id,
            nights=request.nights,
            idempotency_key=request.idempotency_key,
        )
    except asyncpg.UniqueViolationError:
        existing = await db.get_trip_by_idempotency_key(request.idempotency_key)
        if existing is None:
            raise HTTPException(status_code=500, detail="Idempotency key conflict but trip not found")
        if existing["status"] not in ("CONFIRMED", "PENDING"):
            raise HTTPException(
                status_code=502,
                detail={"trip_id": str(existing["id"]), "error": existing["error_message"]},
            )
        return existing
    trip_id = trip["id"]

    try:
        # INTENTIONAL NAIVE DESIGN:
        # This is a plain sequence of remote calls. There is no saga state
        # machine, compensation, TCC, 2PC, retry policy, or idempotency key.
        flight_booking = await clients.book_flight(
            flight_id=request.flight_id,
            trip_id=str(trip_id),
            traveler_name=request.traveler_name,
            delay_after_check_ms=request.simulate.flight_delay_after_check_ms,
        )
        trip = await db.update_trip(
            trip_id, flight_booking_id=UUID(flight_booking["id"])
        )

        hotel_reservation = await clients.reserve_hotel(
            hotel_id=request.hotel_id,
            trip_id=str(trip_id),
            traveler_name=request.traveler_name,
            nights=request.nights,
            delay_after_check_ms=request.simulate.hotel_delay_after_check_ms,
            force_fail=request.simulate.hotel_force_fail,
        )
        trip = await db.update_trip(
            trip_id, hotel_reservation_id=UUID(hotel_reservation["id"])
        )

        flight = await clients.get_flight(request.flight_id)
        hotel = await clients.get_hotel(request.hotel_id)
        amount_cents = calculate_amount_cents(
            flight_price_cents=flight["price_cents"],
            hotel_price_per_night_cents=hotel["price_per_night_cents"],
            nights=request.nights,
        )
        trip = await db.update_trip(trip_id, amount_cents=amount_cents)

        payment = await clients.authorize_payment(
            trip_id=str(trip_id),
            amount_cents=amount_cents,
            force_decline=request.simulate.payment_force_decline,
            force_error=request.simulate.payment_force_error,
            delay_ms=request.simulate.payment_delay_ms,
        )
        trip = await db.update_trip(
            trip_id,
            payment_authorization_id=UUID(payment["id"]),
            status="CONFIRMED",
            error_message=None,
        )

    except Exception as exc:
        trip = await db.update_trip(trip_id, status="COMPENSATING", error_message=str(exc))

        compensation_error = None
        try:
            if trip["flight_booking_id"]:
                await clients.cancel_flight_booking(str(trip["flight_booking_id"]))
            if trip["hotel_reservation_id"]:
                await clients.cancel_hotel_reservation(str(trip["hotel_reservation_id"]))
            trip = await db.update_trip(trip_id, status="COMPENSATED")
        except Exception as comp_exc:
            compensation_error = comp_exc
            trip = await db.update_trip(
                trip_id,
                status="COMPENSATION_FAILED",
                error_message=str(comp_exc),
            )

        raise HTTPException(
            status_code=502,
            detail={
                "trip_id": str(trip_id),
                "error": str(exc),
                "compensation": "COMPENSATED" if compensation_error is None else "COMPENSATION_FAILED",
            },
        )

    try:
        await events.publish_confirmation(
            trip, publish_twice=request.simulate.publish_event_twice
        )
    except Exception:
        # INTENTIONAL NAIVE DESIGN:
        # The trip is already confirmed. There is no transactional outbox to
        # guarantee that the notification event will eventually be published.
        logging.exception("Failed to publish trip.confirmed event")

    return trip