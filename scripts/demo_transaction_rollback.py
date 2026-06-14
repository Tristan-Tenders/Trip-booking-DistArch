from common import FLIGHT_URL, pretty, reset_all

import httpx


def main() -> None:
    reset_all()

    with httpx.Client(timeout=10) as client:
        before = client.get(
            f"{FLIGHT_URL}/flights/FL-ONE-SEAT"
        ).json()

        print("=== BEFORE ===")
        print(pretty(before))

        response = client.post(
            f"{FLIGHT_URL}/flights/FL-ONE-SEAT/bookings",
            json={
                "trip_id": "11111111-1111-1111-1111-111111111111",
                "traveler_name": "Ada Lovelace",
                "seats": 1,
                "fail_after_decrement": True,
            },
        )

        print()
        print("Booking response:")
        print(response.status_code)
        print(response.text)

        after = client.get(
            f"{FLIGHT_URL}/flights/FL-ONE-SEAT"
        ).json()

        print()
        print("=== AFTER ===")
        print(pretty(after))

        if after["seats_available"] == before["seats_available"]:
            print()
            print("PASS: transaction rolled back")
        else:
            print()
            print("FAIL: inventory changed despite failure")


if __name__ == "__main__":
    main()