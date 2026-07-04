import pytest
import sys
import os
import json
import os
sys.path.append('../Assignment_02')
from fastapi.testclient import TestClient
from httpx import AsyncClient
import jwt
from fastapi.testclient import TestClient
from backend.main import app
from backend import schema
from datetime import timedelta
from jose import jwt
import os
import json
from datetime import datetime


client = TestClient(app)


def generate_test_access_token():
    test_user_email = "test@example.com"
    token_expiration = timedelta(hours=24)

    to_encode = {"exp": (datetime.utcnow() + token_expiration).timestamp(), "sub": test_user_email}
    encoded_jwt = jwt.encode(to_encode, os.environ.get("SECRET_KEY"), algorithm=os.environ.get("ALGORITHM"))

    return encoded_jwt


def test_find_optimal_pairs():
    input_data = {
        "locations": [
            "Wild Florida Airboats & Gator Park Florida",
            "Edison & Ford Winter Estates Florida",
            "The John and Mable Ringling Museum of Art Florida",
            "The Dalí (Salvador Dalí Museum) Florida",
            "Universal's Islands of Adventure Florida"
        ]
    }

    access_token = generate_test_access_token()
    headers = {"Authorization": f"Bearer {access_token}"}

    response = client.post("/FindOptimalPairs", json=input_data, headers=headers)

    # Rest of the function remains the same
    assert response.status_code == 200

    response_data = response.json()
    assert "data" in response_data
    assert "status_code" in response_data
    assert response_data["status_code"] == "200"


def test_get_top_attractions():
    input_data = {
        "city": "Orlando Florida",
        "types": "tourist_attraction|amusement_park|park|point_of_interest|establishment"
    }

    access_token = generate_test_access_token()
    headers = {"Authorization": f"Bearer {access_token}"}

    response = client.post("/GetTopAttractions", json=input_data, headers=headers)

    assert response.status_code == 200

    response_data = response.json()
    assert "data" in response_data
    assert "status_code" in response_data
    assert response_data["status_code"] == "200"
    assert len(response_data["data"]) >= 10