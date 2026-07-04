"""Top attractions lookup: Google Places when a key is configured, otherwise a
deterministic static fallback so the app works keyless."""
import httpx

from app.config import get_settings
from app.core.cache import attractions_cache
from app.schemas import AttractionOut

PLACES_URL = "https://maps.googleapis.com/maps/api/place/textsearch/json"

DEFAULT_TYPES = "tourist_attraction|amusement_park|park|point_of_interest|establishment"

_FALLBACK_TEMPLATES = [
    ("{city} Old Town", 4.7), ("{city} Central Park", 4.6),
    ("{city} History Museum", 4.5), ("{city} Botanical Gardens", 4.5),
    ("{city} Art Gallery", 4.4), ("{city} Waterfront Promenade", 4.4),
    ("{city} Observation Tower", 4.3), ("{city} Grand Market", 4.3),
    ("{city} Science Center", 4.2), ("{city} Cathedral Square", 4.2),
]


async def get_top_attractions(city: str, types: str = DEFAULT_TYPES) -> list[AttractionOut]:
    key = (city.lower(), types)
    if key in attractions_cache:
        return attractions_cache[key]

    settings = get_settings()
    if settings.google_maps_api_key:
        results = await _google_places(city, types, settings.google_maps_api_key)
    else:
        results = _static_fallback(city)

    attractions_cache[key] = results
    return results


async def _google_places(city: str, types: str, api_key: str) -> list[AttractionOut]:
    async with httpx.AsyncClient(timeout=15) as client:
        resp = await client.get(
            PLACES_URL,
            params={"query": f"top attractions in {city}", "type": types, "key": api_key},
        )
        resp.raise_for_status()
        data = resp.json()

    places = sorted(
        data.get("results", []), key=lambda p: (p.get("rating") or 0), reverse=True
    )[:10]
    return [
        AttractionOut(
            name=p["name"],
            rating=p.get("rating"),
            address=p.get("formatted_address"),
        )
        for p in places
    ]


def _static_fallback(city: str) -> list[AttractionOut]:
    return [
        AttractionOut(name=name.format(city=city.title()), rating=rating)
        for name, rating in _FALLBACK_TEMPLATES
    ]
