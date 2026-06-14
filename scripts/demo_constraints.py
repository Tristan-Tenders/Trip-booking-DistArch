from common import reset_all, FLIGHT_URL, HOTEL_URL, pretty
import httpx


def main() -> None:
    reset_all()

    with httpx.Client(timeout=10) as client:
        print("=== INITIAL STATE ===")

        flights = client.get(f"{FLIGHT_URL}/flights").json()
        hotels = client.get(f"{HOTEL_URL}/hotels").json()

        print("Flights:")
        print(pretty(flights))
        print()
        print("Hotels:")
        print(pretty(hotels))

        print("\n=== ATTEMPT INVALID UPDATES ===")

        # Try to break flight constraint
        try:
            res = client.post(
                f"{FLIGHT_URL}/flights/FL-ONE-SEAT/bookings",
                json={
                    "trip_id": "11111111-1111-1111-1111-111111111111",
                    "traveler_name": "Constraint Test",
                    "seats": 999,  # forces negative availability
                },
            )
            print("Flight response:")
            print(res.status_code, res.text)
        except Exception as e:
            print("Flight constraint triggered:", str(e))

        # Try to break hotel constraint
        try:
            res = client.post(
                f"{HOTEL_URL}/hotels/HT-ONE-ROOM/reservations",
                json={
                    "trip_id": "11111111-1111-1111-1111-111111111111",
                    "traveler_name": "Constraint Test",
                    "rooms": 999,  # forces negative availability
                    "nights": 1,
                },
            )
            print("Hotel response:")
            print(res.status_code, res.text)
        except Exception as e:
            print("Hotel constraint triggered:", str(e))

        print("\n=== FINAL STATE ===")

        flights_after = client.get(f"{FLIGHT_URL}/flights").json()
        hotels_after = client.get(f"{HOTEL_URL}/hotels").json()

        print("Flights:")
        print(pretty(flights_after))
        print()
        print("Hotels:")
        print(pretty(hotels_after))


if __name__ == "__main__":
    main()