"""Cheapest hotel+flight bundle within budget, ported from the legacy
create_date_pairs sweep in backend/main.py / booking.py (pandas removed).

Tries every valid (start, end) window of `num_days` nights inside the user's
date range and picks the lowest total; flights are ranked by the selected type.
"""
from datetime import date, timedelta

from app.config import get_settings
from app.core.cache import pricing_cache
from app.providers.base import FlightOffer, FlightProvider, HotelOffer, HotelProvider
from app.providers.mock import MockFlightProvider, MockHotelProvider
from app.schemas import EstimateOut, EstimateRequest


def get_providers() -> tuple[FlightProvider, HotelProvider]:
    if get_settings().pricing_provider == "amadeus":
        from app.providers.amadeus import AmadeusFlightProvider, AmadeusHotelProvider

        return AmadeusFlightProvider(), AmadeusHotelProvider()
    return MockFlightProvider(), MockHotelProvider()


def _date_windows(start: date, end: date, num_days: int) -> list[tuple[date, date]]:
    windows = []
    current = start
    while current + timedelta(days=num_days) <= end + timedelta(days=1):
        windows.append((current, current + timedelta(days=num_days)))
        current += timedelta(days=1)
    return windows or [(start, end)]


def _pick_flight(offers: list[FlightOffer], flight_type: str) -> FlightOffer | None:
    if not offers:
        return None
    if flight_type == "Cheapest":
        return min(offers, key=lambda o: o.price)
    if flight_type == "Fastest":
        return min(offers, key=lambda o: o.duration_minutes)
    if flight_type == "Direct":
        direct = [o for o in offers if o.stops == 0]
        return min(direct, key=lambda o: o.price) if direct else min(offers, key=lambda o: o.price)
    # "Best": balance price and duration
    return min(offers, key=lambda o: o.price + o.duration_minutes * 0.5)


async def estimate_trip(req: EstimateRequest) -> EstimateOut | None:
    cache_key = req.model_dump_json()
    if cache_key in pricing_cache:
        return pricing_cache[cache_key]

    flight_provider, hotel_provider = get_providers()

    best: EstimateOut | None = None
    for checkin, checkout in _date_windows(req.start_date, req.end_date, req.num_days):
        flights = await flight_provider.search(
            req.origin_iata, req.destination_iata, checkin, checkout, req.adults
        )
        hotels = await hotel_provider.search(
            req.destination_city, checkin, checkout, req.adults, req.rooms
        )
        flight = _pick_flight(flights, req.flight_type)
        hotel = min(hotels, key=lambda h: h.total_price) if hotels else None
        if flight is None or hotel is None:
            continue

        total = round(flight.price + hotel.total_price, 2)
        if best is None or total < best.total_cost:
            best = EstimateOut(
                start_date=checkin,
                end_date=checkout,
                hotel_name=hotel.name,
                hotel_price=hotel.total_price,
                airline=flight.airline,
                flight_price=flight.price,
                total_cost=total,
                within_budget=total <= req.budget,
            )
        # If a window already fits the budget, prefer the cheapest among fitting ones.

    if best is not None:
        pricing_cache[cache_key] = best
    return best
