from fastapi import APIRouter, Depends, HTTPException, Request, Response, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.security import (
    REFRESH_COOKIE,
    clear_auth_cookies,
    decode_token,
    get_current_user,
    hash_password,
    set_auth_cookies,
    verify_password,
)
from app.db.models import Interest, Plan, User
from app.db.session import get_db
from app.schemas import LoginRequest, ResetPasswordRequest, SignupRequest, UserOut

router = APIRouter(prefix="/auth", tags=["auth"])


def _user_out(user: User) -> UserOut:
    return UserOut(
        id=user.id,
        email=user.email,
        name=user.name,
        role=user.role,
        plan_name=user.plan_name,
        hits_left=user.hits_left,
        interests=[i.place_type for i in user.interests],
    )


@router.post("/signup", status_code=status.HTTP_201_CREATED, response_model=UserOut)
def signup(body: SignupRequest, db: Session = Depends(get_db)):
    if db.scalar(select(User).where(User.email == body.email)):
        raise HTTPException(status.HTTP_409_CONFLICT, "An account with this email already exists")
    plan = db.get(Plan, body.plan)
    if plan is None:
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_ENTITY, f"Unknown plan '{body.plan}'")

    user = User(
        email=body.email,
        hashed_password=hash_password(body.password),
        name=body.name,
        plan_name=plan.name,
        hits_left=plan.api_limit,
        interests=[Interest(place_type=t) for t in body.interests],
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return _user_out(user)


@router.post("/login", response_model=UserOut)
def login(body: LoginRequest, response: Response, db: Session = Depends(get_db)):
    user = db.scalar(select(User).where(User.email == body.email))
    if user is None or not verify_password(body.password, user.hashed_password):
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Incorrect email or password")
    set_auth_cookies(response, user.email)
    return _user_out(user)


@router.post("/refresh", response_model=UserOut)
def refresh(request: Request, response: Response, db: Session = Depends(get_db)):
    token = request.cookies.get(REFRESH_COOKIE)
    if not token:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "No refresh token")
    email = decode_token(token, "refresh")
    user = db.scalar(select(User).where(User.email == email))
    if user is None:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "User no longer exists")
    set_auth_cookies(response, user.email)
    return _user_out(user)


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
def logout(response: Response):
    clear_auth_cookies(response)


@router.post("/forgot-password", status_code=status.HTTP_204_NO_CONTENT)
def forgot_password(body: ResetPasswordRequest, db: Session = Depends(get_db)):
    # Demo-grade reset (no email verification) — kept from the original app; see README.
    user = db.scalar(select(User).where(User.email == body.email))
    if user is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "No account with this email")
    user.hashed_password = hash_password(body.new_password)
    db.commit()


@router.get("/me", response_model=UserOut)
def me(user: User = Depends(get_current_user)):
    return _user_out(user)
