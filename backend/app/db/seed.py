"""Seed plans and an admin user. Idempotent.

Usage: python -m app.db.seed
"""
from sqlalchemy import select

from app.config import get_settings
from app.core.security import hash_password
from app.db.models import Base, Plan, User
from app.db.session import SessionLocal, engine

PLAN_TIERS = {"Basic": 10, "Standard": 25, "Premium": 50}


def seed() -> None:
    Base.metadata.create_all(engine)
    settings = get_settings()
    with SessionLocal() as db:
        for name, limit in PLAN_TIERS.items():
            if db.get(Plan, name) is None:
                db.add(Plan(name=name, api_limit=limit))

        admin = db.scalar(select(User).where(User.email == settings.seed_admin_email))
        if admin is None:
            db.add(
                User(
                    email=settings.seed_admin_email,
                    hashed_password=hash_password(settings.seed_admin_password),
                    name="Admin",
                    role="admin",
                    plan_name="Premium",
                    hits_left=PLAN_TIERS["Premium"],
                )
            )
        db.commit()
    print("Seed complete: plans + admin user.")


if __name__ == "__main__":
    seed()
