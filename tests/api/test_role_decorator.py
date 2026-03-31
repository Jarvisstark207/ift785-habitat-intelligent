"""
Tests API - Décorateur @require_role sur les endpoints (Itération 8)
Vérifie le contrôle d'accès basé sur les rôles depuis provided_auth.
"""

import pytest
from fastapi.testclient import TestClient

from app import app
from domain.models.device_registry import DeviceRegistry

ADMIN_HEADERS = {"Authorization": "Bearer token_admin"}
USER_HEADERS = {"Authorization": "Bearer token_user"}
GUEST_HEADERS = {"Authorization": "Bearer token_guest"}
INVALID_HEADERS = {"Authorization": "Bearer token_invalid"}

client = TestClient(app)


@pytest.fixture(autouse=True)
def clear_registry():
    registry = DeviceRegistry.get_instance()
    registry.clear()
    yield
    registry.clear()


# ---------------------------------------------------------------------------
# Tokens valides - accès autorisé
# ---------------------------------------------------------------------------

class TestAuthorizedAccess:
    def test_admin_accesses_admin_create(self):
        payload = {
            "device_id": "auth_test_1",
            "name": "Auth Device",
            "room_name": "Lab",
            "device_type": "light",
        }
        response = client.post(
            "/api/devices/admin/create", json=payload, headers=ADMIN_HEADERS
        )
        assert response.status_code == 200

    def test_admin_accesses_admin_list(self):
        response = client.get("/api/devices/admin/list", headers=ADMIN_HEADERS)
        assert response.status_code == 200

    def test_admin_token_has_highest_role(self):
        response = client.get("/api/devices/admin/list", headers=ADMIN_HEADERS)
        assert response.status_code == 200


# ---------------------------------------------------------------------------
# Tokens insuffisants - accès refusé (403)
# ---------------------------------------------------------------------------

class TestInsufficientRole:
    def test_guest_blocked_from_admin_create(self):
        payload = {
            "device_id": "blocked_1",
            "name": "Blocked",
            "room_name": "Room",
            "device_type": "light",
        }
        response = client.post(
            "/api/devices/admin/create", json=payload, headers=GUEST_HEADERS
        )
        assert response.status_code == 403

    def test_user_blocked_from_admin_create(self):
        payload = {
            "device_id": "blocked_2",
            "name": "Blocked",
            "room_name": "Room",
            "device_type": "light",
        }
        response = client.post(
            "/api/devices/admin/create", json=payload, headers=USER_HEADERS
        )
        assert response.status_code == 403

    def test_guest_blocked_from_admin_list(self):
        response = client.get("/api/devices/admin/list", headers=GUEST_HEADERS)
        assert response.status_code == 403

    def test_user_blocked_from_admin_list(self):
        response = client.get("/api/devices/admin/list", headers=USER_HEADERS)
        assert response.status_code == 403


# ---------------------------------------------------------------------------
# Token absent ou invalide - 401
# ---------------------------------------------------------------------------

class TestMissingOrInvalidToken:
    def test_no_token_admin_create_returns_401_or_403(self):
        payload = {
            "device_id": "no_token_1",
            "name": "No Token",
            "room_name": "Room",
            "device_type": "light",
        }
        response = client.post("/api/devices/admin/create", json=payload)
        assert response.status_code in (401, 403)

    def test_no_token_admin_list_returns_401_or_403(self):
        response = client.get("/api/devices/admin/list")
        assert response.status_code in (401, 403)

    def test_invalid_token_admin_create_returns_401(self):
        payload = {
            "device_id": "invalid_1",
            "name": "Invalid Token",
            "room_name": "Room",
            "device_type": "light",
        }
        response = client.post(
            "/api/devices/admin/create", json=payload, headers=INVALID_HEADERS
        )
        assert response.status_code == 401

    def test_invalid_token_admin_list_returns_401(self):
        response = client.get("/api/devices/admin/list", headers=INVALID_HEADERS)
        assert response.status_code == 401
