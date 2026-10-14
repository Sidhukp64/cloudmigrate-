import pytest
from fastapi import status


class TestAuthLogin:
    def test_login_success(self, client, admin_user):
        response = client.post("/api/v1/auth/login", json={
            "email": "admin@cloudmigrate.io",
            "password": "AdminPass123!"
        })
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert "access_token" in data
        assert data["token_type"] == "bearer"
        assert data["user"]["email"] == "admin@cloudmigrate.io"

    def test_login_wrong_password(self, client, admin_user):
        response = client.post("/api/v1/auth/login", json={
            "email": "admin@cloudmigrate.io",
            "password": "WrongPassword"
        })
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_login_nonexistent_user(self, client):
        response = client.post("/api/v1/auth/login", json={
            "email": "nobody@nowhere.com",
            "password": "SomePassword"
        })
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_get_me_authenticated(self, client, admin_user, admin_token):
        response = client.get("/api/v1/auth/me", headers={"Authorization": f"Bearer {admin_token}"})
        assert response.status_code == status.HTTP_200_OK
        assert response.json()["email"] == admin_user.email

    def test_get_me_no_token(self, client):
        response = client.get("/api/v1/auth/me")
        assert response.status_code == status.HTTP_403_FORBIDDEN
