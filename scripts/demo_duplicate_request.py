from common import base_trip_payload, create_trip, get_state, pretty, reset_all


def main() -> None:
    reset_all()

    print("=== WITHOUT idempotency key (baseline behavior) ===")
    payload_no_key = base_trip_payload()
    first = create_trip(payload_no_key)
    second = create_trip(payload_no_key)
    print(f"First trip id:  {first.json()['id']}")
    print(f"Second trip id: {second.json()['id']}")
    print(f"Same id? {first.json()['id'] == second.json()['id']} (expected: False — two trips created)")

    print()
    reset_all()

    print("=== WITH idempotency key (fixed behavior) ===")
    payload_with_key = base_trip_payload()
    payload_with_key["idempotency_key"] = "client-request-abc-123"

    first = create_trip(payload_with_key)
    second = create_trip(payload_with_key)
    print(f"First trip id:  {first.json()['id']}")
    print(f"Second trip id: {second.json()['id']}")
    print(f"Same id? {first.json()['id'] == second.json()['id']} (expected: True — idempotent)")

    state = get_state()
    trips = state["trip-service"]["trips"]
    bookings = state["flight-service"]["flight_bookings"]
    reservations = state["hotel-service"]["hotel_reservations"]
    payments = state["payment-service"]["payment_authorizations"]
    print(f"Trips in DB:    {len(trips)} (expected: 1)")
    print(f"Flight bookings: {len(bookings)} (expected: 1)")
    print(f"Hotel reservations: {len(reservations)} (expected: 1)")
    print(f"Payment authorizations: {len(payments)} (expected: 1)")


if __name__ == "__main__":
    main()
