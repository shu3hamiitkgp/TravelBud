from unittest.mock import AsyncMock, patch

ESTIMATE = {
    "start_date": "2026-08-01",
    "end_date": "2026-08-04",
    "hotel_name": "New York Grand Hotel",
    "hotel_price": 450.0,
    "airline": "JetBlue",
    "flight_price": 320.0,
    "total_cost": 770.0,
    "within_budget": True,
}
TRIP = {
    "origin_iata": "BOS",
    "destination_iata": "JFK",
    "destination_city": "New York",
    "start_date": "2026-08-01",
    "end_date": "2026-08-10",
    "num_days": 3,
    "adults": 2,
    "rooms": 1,
    "flight_type": "Best",
    "budget": 1500,
}
CREATE_BODY = {
    "estimate": ESTIMATE,
    "trip": TRIP,
    "selected_places": ["Central Park", "Empire State Building", "The Met"],
    "day_plans": [
        {"day": 1, "places": ["Central Park", "The Met"], "distance_km": 1.2},
        {"day": 2, "places": ["Empire State Building"]},
    ],
    "language": "English",
}

FAKE_ITINERARY = "# Day 1\nVisit Central Park and The Met.\n# Day 2\nEmpire State Building."


def _create(client):
    with patch(
        "app.routers.itineraries.generate_itinerary_or_fallback",
        new=AsyncMock(return_value=FAKE_ITINERARY),
    ):
        return client.post("/itineraries", json=CREATE_BODY)


def test_create_itinerary_decrements_hits(client, user):
    resp = _create(client)
    assert resp.status_code == 201, resp.text
    assert resp.json()["content"] == FAKE_ITINERARY
    assert client.get("/auth/me").json()["hits_left"] == user["hits_left"] - 1


def test_hits_exhaustion_returns_429(client, user):
    # Drain remaining hits directly via repeated creates on a Basic plan (10).
    for _ in range(user["hits_left"]):
        assert _create(client).status_code == 201
    resp = _create(client)
    assert resp.status_code == 429


def test_pdf_download(client, user, tmp_path, monkeypatch):
    from app.config import get_settings

    monkeypatch.setattr(get_settings(), "local_storage_dir", str(tmp_path))
    created = _create(client).json()
    resp = client.get(f"/itineraries/{created['id']}/pdf")
    assert resp.status_code == 200
    assert resp.headers["content-type"] == "application/pdf"
    assert resp.content[:5] == b"%PDF-"


def test_itinerary_isolation_between_users(client, user):
    created = _create(client).json()
    client.post(
        "/auth/signup",
        json={"email": "other@example.com", "password": "password123", "name": "Other"},
    )
    client.post("/auth/login", json={"email": "other@example.com", "password": "password123"})
    assert client.get(f"/itineraries/{created['id']}").status_code == 404
