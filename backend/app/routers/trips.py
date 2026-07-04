from fastapi import APIRouter, Depends, HTTPException, status

from app.core.security import get_current_user
from app.db.models import User
from app.schemas import AttractionOut, DayPlan, EstimateOut, EstimateRequest, PairsRequest
from app.services.attractions import DEFAULT_TYPES, get_top_attractions
from app.services.pairing import find_optimal_pairs
from app.services.pricing import estimate_trip

router = APIRouter(prefix="/trips", tags=["trips"])


@router.get("/attractions", response_model=list[AttractionOut])
async def attractions(
    city: str, types: str = DEFAULT_TYPES, _: User = Depends(get_current_user)
):
    return await get_top_attractions(city, types)


@router.post("/pairs", response_model=list[DayPlan])
async def pairs(body: PairsRequest, _: User = Depends(get_current_user)):
    # Qualify place names with the city (as the legacy app did) for distance lookups.
    locations = [f"{place}, {body.city}" for place in body.locations]
    try:
        day_plans = await find_optimal_pairs(locations)
    except ValueError as e:
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_ENTITY, str(e))
    # Strip the ", city" suffix back off for display.
    for plan in day_plans:
        plan.places = [p.removesuffix(f", {body.city}") for p in plan.places]
    return day_plans


@router.post("/estimate", response_model=EstimateOut)
async def estimate(body: EstimateRequest, _: User = Depends(get_current_user)):
    if body.end_date < body.start_date:
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_ENTITY, "End date must be after start date")
    if (body.end_date - body.start_date).days + 1 < body.num_days:
        raise HTTPException(
            status.HTTP_422_UNPROCESSABLE_ENTITY,
            "Trip length exceeds the selected date range",
        )
    result = await estimate_trip(body)
    if result is None:
        raise HTTPException(
            status.HTTP_404_NOT_FOUND,
            "No flight and hotel combination found for these dates — try different dates or destination",
        )
    return result
