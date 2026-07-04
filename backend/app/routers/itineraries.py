from fastapi import APIRouter, Depends, HTTPException, Response, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.security import get_current_user
from app.db.models import Itinerary, User, UserActivity
from app.db.session import get_db
from app.providers.storage import get_storage
from app.schemas import ItineraryCreateRequest, ItineraryOut, ItinerarySummary
from app.services.llm import build_itinerary_prompt, generate_itinerary_or_fallback, translate
from app.services.pdf import build_pdf

router = APIRouter(prefix="/itineraries", tags=["itineraries"])


@router.post("", response_model=ItineraryOut, status_code=status.HTTP_201_CREATED)
async def create_itinerary(
    body: ItineraryCreateRequest,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    if user.hits_left <= 0:
        raise HTTPException(
            status.HTTP_429_TOO_MANY_REQUESTS,
            f"You've used all requests on your {user.plan_name} plan — upgrade to continue",
        )

    prompt = build_itinerary_prompt(
        user.name, body.trip, body.estimate, body.selected_places, body.day_plans
    )
    content = await generate_itinerary_or_fallback(
        prompt, user.name, body.trip, body.estimate, body.day_plans
    )
    content = await translate(content, body.language)

    itinerary = Itinerary(
        user_id=user.id,
        destination=body.trip.destination_city,
        language=body.language,
        content=content,
        trip={
            "estimate": body.estimate.model_dump(mode="json"),
            "request": body.trip.model_dump(mode="json"),
            "selected_places": body.selected_places,
            "day_plans": [p.model_dump() for p in body.day_plans],
        },
    )
    user.hits_left -= 1
    db.add(itinerary)
    db.add(
        UserActivity(
            user_id=user.id,
            source=body.trip.origin_iata,
            destination=body.trip.destination_iata,
            start_date=body.trip.start_date,
            end_date=body.trip.end_date,
            duration_days=body.trip.num_days,
            total_people=body.trip.adults,
            budget=body.trip.budget,
        )
    )
    db.commit()
    db.refresh(itinerary)
    return itinerary


@router.get("", response_model=list[ItinerarySummary])
def list_itineraries(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    return db.scalars(
        select(Itinerary)
        .where(Itinerary.user_id == user.id)
        .order_by(Itinerary.created_at.desc())
    ).all()


def _get_owned(itinerary_id: int, user: User, db: Session) -> Itinerary:
    itinerary = db.get(Itinerary, itinerary_id)
    if itinerary is None or itinerary.user_id != user.id:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Itinerary not found")
    return itinerary


@router.get("/{itinerary_id}", response_model=ItineraryOut)
def get_itinerary(
    itinerary_id: int, user: User = Depends(get_current_user), db: Session = Depends(get_db)
):
    return _get_owned(itinerary_id, user, db)


@router.get("/{itinerary_id}/pdf")
def download_pdf(
    itinerary_id: int, user: User = Depends(get_current_user), db: Session = Depends(get_db)
):
    itinerary = _get_owned(itinerary_id, user, db)
    storage = get_storage()

    pdf_bytes = storage.load(itinerary.pdf_key) if itinerary.pdf_key else None
    if pdf_bytes is None:
        pdf_bytes = build_pdf(itinerary.content, itinerary.language)
        key = f"itinerary_{itinerary.id}.pdf"
        storage.save(key, pdf_bytes)
        itinerary.pdf_key = key
        db.commit()

    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={
            "Content-Disposition": f'attachment; filename="TravelBud_{itinerary.destination}_{itinerary.id}.pdf"'
        },
    )
