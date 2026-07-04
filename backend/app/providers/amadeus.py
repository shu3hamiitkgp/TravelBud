"""Amadeus Self-Service (test tier) providers. Opt-in via PRICING_PROVIDER=amadeus.

Uses the test environment (test.api.amadeus.com) — free tier, limited coverage.
"""
import time
from datetime import date

import httpx

from app.config import get_settings
from app.providers.base import FlightOffer, FlightProvider, HotelOffer, HotelProvider

BASE_URL = "https://test.api.amadeus.com"

_token: dict = {"value": None, "expires_at": 0.0}


async def _get_token(client: httpx.AsyncClient) -> str:
    if _token["value"] and time.time() < _token["expires_at"] - 60:
        return _token["value"]
    settings = get_settings()
    resp = await client.post(
        f"{BASE_URL}/v1/security/oauth2/token",
        data={
            "grant_type": "client_credentials",
            "client_id": settings.amadeus_client_id,
            "client_secret": settings.amadeus_client_secret,
        },
    )
    resp.raise_for_status()
    data = resp.json()
    _token["value"] = data["access_token"]
    _token["expires_at"] = time.time() + data.get("expires_in", 1799)
    return _token["value"]


class AmadeusFlightProvider(FlightProvider):
    async def search(
        self, origin: str, destination: str, depart: date, return_: date, adults: int
    ) -> list[FlightOffer]:
        async with httpx.AsyncClient(timeout=30) as client:
            token = await _get_token(client)
            resp = await client.get(
                f"{BASE_URL}/v2/shopping/flight-offers",
                headers={"Authorization": f"Bearer {token}"},
                params={
                    "originLocationCode": origin,
                    "destinationLocationCode": destination,
                    "departureDate": depart.isoformat(),
                    "returnDate": return_.isoformat(),
                    "adults": adults,
                    "currencyCode": "USD",
                    "max": 10,
                },
            )
            resp.raise_for_status()
            data = resp.json()

        offers = []
        for offer in data.get("data", []):
            itin = offer["itineraries"][0]
            segments = itin["segments"]
            duration = itin.get("duration", "PT0M")  # ISO8601, e.g. PT5H30M
            offers.append(
                FlightOffer(
                    airline=segments[0]["carrierCode"],
                    price=float(offer["price"]["grandTotal"]),
                    duration_minutes=_iso_duration_minutes(duration),
                    stops=len(segments) - 1,
                    depart_date=depart,
                    return_date=return_,
                )
            )
        return offers


class AmadeusHotelProvider(HotelProvider):
    async def search(
        self, city: str, checkin: date, checkout: date, adults: int, rooms: int
    ) -> list[HotelOffer]:
        async with httpx.AsyncClient(timeout=30) as client:
            token = await _get_token(client)
            headers = {"Authorization": f"Bearer {token}"}

            hotels_resp = await client.get(
                f"{BASE_URL}/v1/reference-data/locations/hotels/by-city",
                headers=headers,
                params={"cityCode": city},
            )
            hotels_resp.raise_for_status()
            hotel_ids = [h["hotelId"] for h in hotels_resp.json().get("data", [])[:20]]
            if not hotel_ids:
                return []

            offers_resp = await client.get(
                f"{BASE_URL}/v3/shopping/hotel-offers",
                headers=headers,
                params={
                    "hotelIds": ",".join(hotel_ids),
                    "checkInDate": checkin.isoformat(),
                    "checkOutDate": checkout.isoformat(),
                    "adults": adults,
                    "roomQuantity": rooms,
                    "currency": "USD",
                },
            )
            offers_resp.raise_for_status()
            data = offers_resp.json()

        results = []
        for entry in data.get("data", []):
            hotel_offers = entry.get("offers", [])
            if not hotel_offers:
                continue
            results.append(
                HotelOffer(
                    name=entry["hotel"].get("name", "Hotel"),
                    total_price=float(hotel_offers[0]["price"]["total"]),
                    checkin=checkin,
                    checkout=checkout,
                )
            )
        return results


def _iso_duration_minutes(duration: str) -> int:
    hours = minutes = 0
    body = duration.removeprefix("PT")
    if "H" in body:
        h, body = body.split("H", 1)
        hours = int(h)
    if "M" in body:
        minutes = int(body.rstrip("M") or 0)
    return hours * 60 + minutes
