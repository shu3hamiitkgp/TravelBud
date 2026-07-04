"""Deterministic mock pricing so the app runs end-to-end with zero paid keys.

Prices are seeded from a hash of the route/city and dates, so repeated searches
return identical results and different inputs give plausible variety.
"""
import hashlib
from datetime import date

from app.providers.base import FlightOffer, FlightProvider, HotelOffer, HotelProvider

_AIRLINES = ["Delta", "United", "American Airlines", "JetBlue", "Lufthansa", "Emirates"]
_HOTEL_STYLES = ["Grand Hotel", "City Inn", "Riverside Suites", "Plaza Hotel", "Boutique Stay"]


def _seed(*parts: object) -> int:
    digest = hashlib.sha256("|".join(str(p) for p in parts).encode()).digest()
    return int.from_bytes(digest[:8], "big")


class MockFlightProvider(FlightProvider):
    async def search(
        self, origin: str, destination: str, depart: date, return_: date, adults: int
    ) -> list[FlightOffer]:
        seed = _seed("flight", origin, destination, depart, return_)
        offers = []
        for i in range(4):
            s = _seed(seed, i)
            base = 120 + (s % 400)
            offers.append(
                FlightOffer(
                    airline=_AIRLINES[s % len(_AIRLINES)],
                    price=round(base * adults * (1 + i * 0.12), 2),
                    duration_minutes=90 + (s % 600),
                    stops=i % 3,
                    depart_date=depart,
                    return_date=return_,
                )
            )
        return offers


class MockHotelProvider(HotelProvider):
    async def search(
        self, city: str, checkin: date, checkout: date, adults: int, rooms: int
    ) -> list[HotelOffer]:
        nights = max((checkout - checkin).days, 1)
        seed = _seed("hotel", city.lower(), checkin, checkout)
        offers = []
        for i in range(5):
            s = _seed(seed, i)
            nightly = 70 + (s % 220)
            offers.append(
                HotelOffer(
                    name=f"{city.title()} {_HOTEL_STYLES[s % len(_HOTEL_STYLES)]}",
                    total_price=round(nightly * nights * rooms, 2),
                    rating=round(3.5 + (s % 15) / 10, 1),
                    checkin=checkin,
                    checkout=checkout,
                )
            )
        return offers
