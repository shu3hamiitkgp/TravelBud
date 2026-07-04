"""Greedy nearest-pair day planner, ported from legacy google_maps.find_optimal_pairs.

Pairs the two closest unvisited attractions per day; leftovers go on the last day.
Distances come from the Google Distance Matrix when a key is configured, otherwise
a deterministic pseudo-distance so the flow works keyless.
"""
import hashlib
from itertools import combinations

import httpx

from app.config import get_settings
from app.core.cache import distance_cache
from app.schemas import DayPlan

DISTANCE_URL = "https://maps.googleapis.com/maps/api/distancematrix/json"


async def _distance_km(a: str, b: str) -> float:
    key = tuple(sorted((a, b)))
    if key in distance_cache:
        return distance_cache[key]

    settings = get_settings()
    if settings.google_maps_api_key:
        async with httpx.AsyncClient(timeout=15) as client:
            resp = await client.get(
                DISTANCE_URL,
                params={"origins": a, "destinations": b, "key": settings.google_maps_api_key},
            )
            resp.raise_for_status()
            element = resp.json()["rows"][0]["elements"][0]
            if element.get("status") != "OK":
                raise ValueError(f"No route between {a!r} and {b!r}")
            km = element["distance"]["value"] / 1000
    else:
        # Deterministic pseudo-distance (1–15 km) from the pair's hash.
        digest = hashlib.sha256("|".join(key).encode()).digest()
        km = 1 + (int.from_bytes(digest[:4], "big") % 1400) / 100

    distance_cache[key] = km
    return km


async def find_optimal_pairs(locations: list[str]) -> list[DayPlan]:
    distances = {
        pair: await _distance_km(*pair) for pair in combinations(locations, 2)
    }

    visited: set[str] = set()
    day_plans: list[DayPlan] = []
    day = 1
    for pair, km in sorted(distances.items(), key=lambda x: x[1]):
        if pair[0] not in visited and pair[1] not in visited:
            day_plans.append(DayPlan(day=day, places=list(pair), distance_km=round(km, 2)))
            visited.update(pair)
            day += 1

    left_out = [loc for loc in locations if loc not in visited]
    if left_out:
        day_plans.append(DayPlan(day=day, places=left_out))

    return day_plans
