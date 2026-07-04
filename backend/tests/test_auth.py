def test_signup_login_me_roundtrip(client):
    resp = client.post(
        "/auth/signup",
        json={
            "email": "a@example.com",
            "password": "password123",
            "name": "Alice",
            "plan": "Standard",
            "interests": ["museum"],
        },
    )
    assert resp.status_code == 201
    body = resp.json()
    assert body["plan_name"] == "Standard"
    assert body["hits_left"] == 25
    assert "hashed_password" not in body

    resp = client.post("/auth/login", json={"email": "a@example.com", "password": "password123"})
    assert resp.status_code == 200
    assert "access_token" in resp.cookies

    resp = client.get("/auth/me")
    assert resp.status_code == 200
    assert resp.json()["email"] == "a@example.com"
    assert resp.json()["interests"] == ["museum"]


def test_login_wrong_password(client, user):
    resp = client.post(
        "/auth/login", json={"email": "traveler@example.com", "password": "wrong-password"}
    )
    assert resp.status_code == 401


def test_duplicate_signup_rejected(client, user):
    resp = client.post(
        "/auth/signup",
        json={"email": "traveler@example.com", "password": "password123", "name": "Dup"},
    )
    assert resp.status_code == 409


def test_me_requires_auth(client):
    assert client.get("/auth/me").status_code == 401


def test_forgot_password_resets(client, user):
    resp = client.post(
        "/auth/forgot-password",
        json={"email": "traveler@example.com", "new_password": "newpassword1"},
    )
    assert resp.status_code == 204
    assert (
        client.post(
            "/auth/login", json={"email": "traveler@example.com", "password": "newpassword1"}
        ).status_code
        == 200
    )


def test_admin_endpoint_forbidden_for_user(client, user):
    resp = client.get("/admin/analytics")
    assert resp.status_code == 403
