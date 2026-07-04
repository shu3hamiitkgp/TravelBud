from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.security import get_current_user
from app.db.models import Interest, Plan, User
from app.db.session import get_db
from app.routers.auth import _user_out
from app.schemas import AccountUpdateRequest, UserOut

router = APIRouter(prefix="/account", tags=["account"])

# Curated subset of Google place types relevant to travel interests
# (full list lived in legacy google_maps.get_place_types).
PLACE_TYPES = [
    "amusement_park", "aquarium", "art_gallery", "bakery", "bar", "cafe",
    "campground", "casino", "church", "hindu_temple", "library", "mosque",
    "museum", "night_club", "park", "restaurant", "shopping_mall", "spa",
    "stadium", "synagogue", "tourist_attraction", "zoo",
]


@router.get("/place-types", response_model=list[str])
def place_types():
    return PLACE_TYPES


@router.patch("", response_model=UserOut)
def update_account(
    body: AccountUpdateRequest,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    if body.plan is not None:
        plan = db.get(Plan, body.plan)
        if plan is None:
            raise HTTPException(status.HTTP_422_UNPROCESSABLE_ENTITY, f"Unknown plan '{body.plan}'")
        if plan.name != user.plan_name:
            user.plan_name = plan.name
            user.hits_left = plan.api_limit

    if body.interests is not None:
        user.interests.clear()
        user.interests.extend(Interest(place_type=t) for t in body.interests)

    db.commit()
    db.refresh(user)
    return _user_out(user)
