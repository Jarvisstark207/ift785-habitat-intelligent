"""Tests API pour les endpoints d'authentification - Iteration 7"""

import sys
import pytest
from fastapi.testclient import TestClient


@pytest.fixture(autouse=True)
def reset_store():
    # app.py est charge sous le nom app_py_module via app/__init__.py
    from app import app  # noqa: F401 - force le chargement du module
    root = sys.modules.get("app_py_module")
    if root and hasattr(root, "_auth_service"):
        root._auth_service._store.clear()
    yield
    if root and hasattr(root, "_auth_service"):
        root._auth_service._store.clear()


@pytest.fixture
def client():
    from app import app
    return TestClient(app, raise_server_exceptions=False)


class TestRegisterEndpoint:
    def test_register_success(self, client):
        res = client.post("/api/auth/register", json={
            "username": "alice", "password": "pwd123", "role": "user"
        })
        assert res.status_code == 200
        data = res.json()
        assert data["status"] == "ok"
        assert data["user"]["username"] == "alice"

    def test_register_duplicate_returns_error(self, client):
        client.post("/api/auth/register", json={"username": "alice", "password": "pwd"})
        res = client.post("/api/auth/register", json={"username": "alice", "password": "pwd"})
        assert res.json()["status"] == "error"

    def test_register_invalid_role_returns_error(self, client):
        res = client.post("/api/auth/register", json={
            "username": "alice", "password": "pwd", "role": "superadmin"
        })
        assert res.json()["status"] == "error"


class TestLoginEndpoint:
    def test_login_success(self, client):
        client.post("/api/auth/register", json={"username": "alice", "password": "pwd"})
        res = client.post("/api/auth/login", json={"username": "alice", "password": "pwd"})
        assert res.status_code == 200
        data = res.json()
        assert "token" in data
        assert data["status"] == "ok"

    def test_login_wrong_password(self, client):
        client.post("/api/auth/register", json={"username": "alice", "password": "pwd"})
        res = client.post("/api/auth/login", json={"username": "alice", "password": "wrong"})
        assert res.json()["status"] == "error"

    def test_login_unknown_user(self, client):
        res = client.post("/api/auth/login", json={"username": "nobody", "password": "pwd"})
        assert res.json()["status"] == "error"


class TestMeEndpoint:
    def test_me_with_valid_token(self, client):
        res = client.get("/api/auth/me", headers={"Authorization": "Bearer token_admin"})
        assert res.status_code == 200
        data = res.json()
        assert "user" in data
        assert data["user"]["role"] == "admin"

    def test_me_without_token_returns_401(self, client):
        res = client.get("/api/auth/me")
        assert res.status_code == 401

    def test_me_with_invalid_token_returns_401(self, client):
        res = client.get("/api/auth/me", headers={"Authorization": "Bearer bad_token"})
        assert res.status_code == 401


class TestUserEndpoints:
    def test_get_user_devices_authenticated(self, client):
        res = client.get(
            "/api/users/admin_user/devices",
            headers={"Authorization": "Bearer token_admin"},
        )
        assert res.status_code == 200
        data = res.json()
        assert "devices" in data

    def test_get_user_permissions_authenticated(self, client):
        res = client.get(
            "/api/users/admin_user/permissions",
            headers={"Authorization": "Bearer token_admin"},
        )
        assert res.status_code == 200
        data = res.json()
        assert "permissions" in data

    def test_get_user_devices_unauthenticated_returns_401(self, client):
        res = client.get("/api/users/some_user/devices")
        assert res.status_code == 401

    def test_user_cannot_access_other_user_devices(self, client):
        res = client.get(
            "/api/users/other_user_id/devices",
            headers={"Authorization": "Bearer token_user"},
        )
        assert res.status_code == 403
