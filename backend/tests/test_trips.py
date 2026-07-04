def test_attractions_keyless_fallback(client, user):
    resp = client.get("/trips/attractions", params={"city": "Paris"})
    assert resp.status_code == 200
    names = [a["name"] for a in resp.json()]
    assert len(names) == 10
    assert any("Paris" in n for n in names)


def test_pairs_greedy_grouping(client, user):
    resp = client.post(
        "/trips/pairs",
        json={"locations": ["Louvre", "Eiffel Tower", "Notre Dame", "Arc de Triomphe", "Pantheon"], "city": "Paris"},
    )
    assert resp.status_code == 200
    plans = resp.json()
    # 5 places -> 2 pairs + 1 leftover day
    assert len(plans) == 3
    paired = [p for p in plans if len(p["places"]) == 2]
    assert len(paired) == 2
    all_places = [place for p in plans for place in p["places"]]
    assert sorted(all_places) == sorted(
        ["Louvre", "Eiffel Tower", "Notre Dame", "Arc de Triomphe", "Pantheon"]
    )


def test_estimate_mock_bundle(client, user):
    resp = client.post(
        "/trips/estimate",
        json={
            "origin_iata": "BOS",
            "destination_iata": "JFK",
            "destination_city": "New York",
            "start_date": "2026-08-01",
            "end_date": "2026-08-10",
            "num_days": 3,
            "adults": 2,
            "rooms": 1,
            "flight_type": "Cheapest",
            "budget": 5000,
        },
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["total_cost"] == round(data["hotel_price"] + data["flight_price"], 2)
    assert data["within_budget"] is True

    # Deterministic: same request returns same bundle
    resp2 = client.post("/trips/estimate", json={
        "origin_iata": "BOS", "destination_iata": "JFK", "destination_city": "New York",
        "start_date": "2026-08-01", "end_date": "2026-08-10", "num_days": 3,
        "adults": 2, "rooms": 1, "flight_type": "Cheapest", "budget": 5000,
    })
    assert resp2.json() == data


def test_estimate_rejects_bad_dates(client, user):
    resp = client.post(
        "/trips/estimate",
        json={
            "origin_iata": "BOS",
            "destination_iata": "JFK",
            "destination_city": "New York",
            "start_date": "2026-08-10",
            "end_date": "2026-08-01",
            "num_days": 3,
            "adults": 1,
            "rooms": 1,
            "flight_type": "Best",
            "budget": 1000,
        },
    )
    assert resp.status_code == 422
