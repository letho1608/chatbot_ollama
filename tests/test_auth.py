"""Auth endpoint tests: register, login, logout, JWT, role check."""

import json


class TestAuth:
    def test_register(self, client):
        resp = client.post("/api/auth/register", json={
            "username": "newuser", "email": "new@test.com", "password": "pass123"
        })
        assert resp.status_code == 200
        data = resp.json()
        assert data["ok"] is True
        assert "token" in data
        assert data["role"] == "user"

    def test_register_duplicate(self, client, admin_user):
        resp = client.post("/api/auth/register", json={
            "username": "admin", "email": "admin@test.local", "password": "admin123"
        })
        assert resp.status_code == 400

    def test_register_short_password(self, client):
        resp = client.post("/api/auth/register", json={
            "username": "shortpwd", "email": "short@test.com", "password": "123"
        })
        assert resp.status_code == 400

    def test_login(self, client, admin_user):
        resp = client.post("/api/auth/login", json={
            "username": "admin", "password": "admin123"
        })
        assert resp.status_code == 200
        data = resp.json()
        assert data["ok"] is True
        assert "token" in data
        assert data["role"] == "admin"

    def test_login_wrong_password(self, client):
        resp = client.post("/api/auth/login", json={
            "username": "admin", "password": "wrongpass"
        })
        assert resp.status_code == 401

    def test_login_nonexistent(self, client):
        resp = client.post("/api/auth/login", json={
            "username": "nobody", "password": "pass123"
        })
        assert resp.status_code == 401

    def test_me_authenticated(self, client, admin_headers):
        resp = client.get("/api/auth/me", headers=admin_headers)
        assert resp.status_code == 200
        data = resp.json()
        assert data["username"] == "admin"
        assert data["role"] == "admin"

    def test_me_no_token(self, client):
        resp = client.get("/api/auth/me")
        assert resp.status_code == 401

    def test_me_invalid_token(self, client):
        resp = client.get("/api/auth/me", headers={"Authorization": "Bearer invalidtoken"})
        assert resp.status_code == 401

    def test_logout(self, client):
        resp = client.post("/api/auth/logout")
        assert resp.status_code == 200
        assert resp.json()["ok"] is True

    def test_token_contains_sub_string(self, admin_token):
        from core.auth import decode_token
        payload = decode_token(admin_token)
        assert payload is not None
        assert isinstance(payload["sub"], str)
