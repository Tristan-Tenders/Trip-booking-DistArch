from common import base_trip_payload, create_trip, get_state, pretty, reset_all


def main() -> None:
    reset_all()
    response = create_trip(base_trip_payload(payment_force_decline=True))

    print("=== BEFORE (naive design) ===")
    print("Payment failed → trip stuck as FAILED, flight and hotel still reserved.")
    print()
    print("=== AFTER (compensation) ===")
    print("Payment failed → trip enters COMPENSATING → flight and hotel cancelled → COMPENSATED.")
    print()
    print("Trip response:")
    print(pretty(response.json()))
    print()
    print("State (verify flight=CANCELLED, hotel=CANCELLED, trip=COMPENSATED):")
    print(pretty(get_state()))


if __name__ == "__main__":
    main()

