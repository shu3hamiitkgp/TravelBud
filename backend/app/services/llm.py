"""Itinerary generation and translation via the Anthropic Claude API.

Replaces the legacy GPT-3.5 (openai 0.27) generation and the mBART-50
torch/transformers translation pipeline.
"""
import anthropic

from app.config import get_settings
from app.schemas import DayPlan, EstimateOut, EstimateRequest

_MAX_TOKENS = 2048


def _client() -> anthropic.AsyncAnthropic:
    return anthropic.AsyncAnthropic(api_key=get_settings().anthropic_api_key)


def build_itinerary_prompt(
    user_name: str,
    trip: EstimateRequest,
    estimate: EstimateOut,
    selected_places: list[str],
    day_plans: list[DayPlan],
) -> str:
    # Adapted from legacy prompt.py:create_itinerary.
    days_section = "\n".join(
        f"- Day {p.day}: {' and '.join(p.places)}"
        + (f" ({p.distance_km} km apart)" if p.distance_km is not None else "")
        for p in day_plans
    )
    return f"""Create a detailed, friendly travel itinerary (~500 words) using ONLY the information below. Do not invent hotels, flights, or prices. Start with a personalized greeting for the traveler by name, present a day-by-day plan in markdown with a heading per day, and end with a short terms-and-conditions note.

Traveler: {user_name}
Trip: {trip.origin_iata} → {trip.destination_iata} ({trip.destination_city})
Dates: {estimate.start_date} to {estimate.end_date} ({trip.num_days} days)
Party: {trip.adults} adult(s), {trip.rooms} room(s)
Budget: ${trip.budget:.2f}

Hotel: {estimate.hotel_name} — ${estimate.hotel_price:.2f}
Flight: {estimate.airline} ({trip.flight_type}) — ${estimate.flight_price:.2f}
Total cost: ${estimate.total_cost:.2f}

Places to visit: {', '.join(selected_places)}

Day-by-day pairing (locations grouped by proximity):
{days_section}

If any listed place is not covered by the day pairing, schedule it on the remaining days."""


def _fallback_itinerary(
    user_name: str,
    trip: EstimateRequest,
    estimate: EstimateOut,
    day_plans: list[DayPlan],
) -> str:
    days = "\n\n".join(
        f"## Day {p.day}\nVisit {' and '.join(p.places)}."
        + (f" They are {p.distance_km} km apart." if p.distance_km is not None else "")
        for p in day_plans
    )
    return f"""# Your {trip.destination_city} Trip

Hello {user_name}! Here is your trip plan from {estimate.start_date} to {estimate.end_date}.

**Flight:** {estimate.airline} — ${estimate.flight_price:.2f}
**Hotel:** {estimate.hotel_name} — ${estimate.hotel_price:.2f}
**Total:** ${estimate.total_cost:.2f}

{days}

*Generated in offline mode — set ANTHROPIC_API_KEY for a full AI-written itinerary.*

**Terms and conditions:** prices are estimates and subject to change at booking time."""


async def generate_itinerary_or_fallback(
    prompt: str,
    user_name: str,
    trip: EstimateRequest,
    estimate: EstimateOut,
    day_plans: list[DayPlan],
) -> str:
    if not get_settings().anthropic_api_key:
        return _fallback_itinerary(user_name, trip, estimate, day_plans)
    return await generate_itinerary(prompt)


async def generate_itinerary(prompt: str) -> str:
    client = _client()
    settings = get_settings()
    last_error: Exception | None = None
    for _ in range(2):  # one retry
        try:
            message = await client.messages.create(
                model=settings.anthropic_model,
                max_tokens=_MAX_TOKENS,
                temperature=0.2,
                messages=[{"role": "user", "content": prompt}],
            )
            return message.content[0].text
        except anthropic.APIError as e:
            last_error = e
    raise last_error


async def translate(text: str, target_language: str) -> str:
    if target_language == "English" or not get_settings().anthropic_api_key:
        return text
    client = _client()
    settings = get_settings()
    message = await client.messages.create(
        model=settings.anthropic_model,
        max_tokens=_MAX_TOKENS,
        temperature=0,
        messages=[
            {
                "role": "user",
                "content": (
                    f"Translate the following travel itinerary into {target_language}. "
                    "Preserve the markdown structure, names of hotels/airlines/places, "
                    "dates, and prices exactly. Reply with only the translation.\n\n"
                    f"{text}"
                ),
            }
        ],
    )
    return message.content[0].text
