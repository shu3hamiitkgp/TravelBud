from abc import ABC, abstractmethod
from datetime import date

from pydantic import BaseModel


class FlightOffer(BaseModel):
    airline: str
    price: float
    duration_minutes: int
    stops: int
    depart_date: date
    return_date: date


class HotelOffer(BaseModel):
    name: str
    total_price: float
    rating: float | None = None
    checkin: date
    checkout: date


class FlightProvider(ABC):
    @abstractmethod
    async def search(
        self, origin: str, destination: str, depart: date, return_: date, adults: int
    ) -> list[FlightOffer]: ...


class HotelProvider(ABC):
    @abstractmethod
    async def search(
        self, city: str, checkin: date, checkout: date, adults: int, rooms: int
    ) -> list[HotelOffer]: ...
