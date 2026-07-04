from datetime import datetime, date

from sqlalchemy import ForeignKey, String, Text, JSON, func
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
    pass


class Plan(Base):
    __tablename__ = "plans"

    name: Mapped[str] = mapped_column(String(32), primary_key=True)
    api_limit: Mapped[int]

    users: Mapped[list["User"]] = relationship(back_populates="plan")


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True)
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    hashed_password: Mapped[str] = mapped_column(String(255))
    name: Mapped[str] = mapped_column(String(255))
    role: Mapped[str] = mapped_column(String(16), default="user")
    plan_name: Mapped[str] = mapped_column(ForeignKey("plans.name"), default="Basic")
    hits_left: Mapped[int] = mapped_column(default=10)
    created_at: Mapped[datetime] = mapped_column(server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(server_default=func.now(), onupdate=func.now())

    plan: Mapped[Plan] = relationship(back_populates="users")
    interests: Mapped[list["Interest"]] = relationship(
        back_populates="user", cascade="all, delete-orphan"
    )
    activities: Mapped[list["UserActivity"]] = relationship(back_populates="user")
    itineraries: Mapped[list["Itinerary"]] = relationship(back_populates="user")


class Interest(Base):
    __tablename__ = "interests"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    place_type: Mapped[str] = mapped_column(String(64))

    user: Mapped[User] = relationship(back_populates="interests")


class UserActivity(Base):
    __tablename__ = "user_activities"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    source: Mapped[str] = mapped_column(String(128))
    destination: Mapped[str] = mapped_column(String(128))
    start_date: Mapped[date]
    end_date: Mapped[date]
    duration_days: Mapped[int]
    total_people: Mapped[int]
    budget: Mapped[float]
    created_at: Mapped[datetime] = mapped_column(server_default=func.now())

    user: Mapped[User] = relationship(back_populates="activities")


class Itinerary(Base):
    __tablename__ = "itineraries"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    destination: Mapped[str] = mapped_column(String(128))
    language: Mapped[str] = mapped_column(String(16), default="English")
    content: Mapped[str] = mapped_column(Text)
    trip: Mapped[dict] = mapped_column(JSON)  # cost breakdown, dates, pairings, places
    pdf_key: Mapped[str | None] = mapped_column(String(512), nullable=True)
    created_at: Mapped[datetime] = mapped_column(server_default=func.now())

    user: Mapped[User] = relationship(back_populates="itineraries")
