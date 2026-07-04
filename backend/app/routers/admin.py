"""Admin analytics — aggregates only, never raw user rows (the legacy endpoint
leaked bcrypt password hashes to any authenticated caller)."""
from fastapi import APIRouter, Depends
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.core.security import require_admin
from app.db.models import User, UserActivity
from app.db.session import get_db

router = APIRouter(prefix="/admin", tags=["admin"], dependencies=[Depends(require_admin)])


@router.get("/analytics")
def analytics(db: Session = Depends(get_db)):
    users_by_plan = dict(
        db.execute(select(User.plan_name, func.count()).group_by(User.plan_name)).all()
    )

    trips_by_day = [
        {"date": str(day), "trips": count}
        for day, count in db.execute(
            select(func.date(UserActivity.created_at), func.count())
            .group_by(func.date(UserActivity.created_at))
            .order_by(func.date(UserActivity.created_at))
        ).all()
    ]

    top_destinations = [
        {"destination": dest, "trips": count}
        for dest, count in db.execute(
            select(UserActivity.destination, func.count())
            .group_by(UserActivity.destination)
            .order_by(func.count().desc())
            .limit(10)
        ).all()
    ]

    budget_stats = db.execute(
        select(
            func.count(UserActivity.id),
            func.avg(UserActivity.budget),
            func.min(UserActivity.budget),
            func.max(UserActivity.budget),
        )
    ).one()

    preferred_dates = [
        {"date": str(day), "travelers": count}
        for day, count in db.execute(
            select(UserActivity.start_date, func.count(func.distinct(UserActivity.user_id)))
            .group_by(UserActivity.start_date)
            .order_by(UserActivity.start_date)
        ).all()
    ]

    return {
        "total_users": db.scalar(select(func.count(User.id))),
        "users_by_plan": users_by_plan,
        "trips_by_day": trips_by_day,
        "top_destinations": top_destinations,
        "budget": {
            "trips": budget_stats[0],
            "avg": float(budget_stats[1] or 0),
            "min": float(budget_stats[2] or 0),
            "max": float(budget_stats[3] or 0),
        },
        "preferred_start_dates": preferred_dates,
    }
