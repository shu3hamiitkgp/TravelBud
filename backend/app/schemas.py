from datetime import date, datetime

from pydantic import BaseModel, EmailStr, Field

PLACE_LANGS = ("English", "Spanish", "Hindi")


# --- Auth / account ---

class SignupRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8)
    name: str = Field(min_length=1, max_length=255)
    plan: str = "Basic"
    interests: list[str] = []


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class ResetPasswordRequest(BaseModel):
    email: EmailStr
    new_password: str = Field(min_length=8)


class UserOut(BaseModel):
    id: int
    email: str
    name: str
    role: str
    plan_name: str
    hits_left: int
    interests: list[str] = []

    model_config = {"from_attributes": True}


class AccountUpdateRequest(BaseModel):
    plan: str | None = None
    interests: list[str] | None = None


# --- Trips ---

class AttractionOut(BaseModel):
    name: str
    rating: float | None = None
    address: str | None = None


class PairsRequest(BaseModel):
    locations: list[str] = Field(min_length=2, max_length=10)
    city: str


class DayPlan(BaseModel):
    day: int
    places: list[str]
    distance_km: float | None = None


class EstimateRequest(BaseModel):
    origin_iata: str = Field(min_length=3, max_length=3)
    destination_iata: str = Field(min_length=3, max_length=3)
    destination_city: str
    start_date: date
    end_date: date
    num_days: int = Field(ge=1, le=365)
    adults: int = Field(ge=1, le=20)
    rooms: int = Field(ge=1, le=10)
    flight_type: str = "Best"  # Best | Cheapest | Fastest | Direct
    budget: float = Field(ge=0)


class EstimateOut(BaseModel):
    start_date: date
    end_date: date
    hotel_name: str
    hotel_price: float
    airline: str
    flight_price: float
    total_cost: float
    within_budget: bool


# --- Itineraries ---

class ItineraryCreateRequest(BaseModel):
    estimate: EstimateOut
    trip: EstimateRequest
    selected_places: list[str] = Field(min_length=1, max_length=10)
    day_plans: list[DayPlan]
    language: str = "English"


class ItinerarySummary(BaseModel):
    id: int
    destination: str
    language: str
    created_at: datetime

    model_config = {"from_attributes": True}


class ItineraryOut(ItinerarySummary):
    content: str
    trip: dict
