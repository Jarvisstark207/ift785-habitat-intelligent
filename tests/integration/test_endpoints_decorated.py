"""
Tests d'intégration - Décorateurs sur les vrais endpoints FastAPI (Itération 8)
Vérifie que @log_call, @validate_input et @require_role fonctionnent sur les endpoints réels.
"""

import pytest
from fastapi.testclient import TestClient

from app import app
from domain.models.device_registry import DeviceRegistry

ADMIN_HEADERS = {"Authorization": "Bearer token_admin"}
USER_HEADERS = {"Authorization": "Bearer token_user"}
GUEST_HEADERS = {"Authorization": "Bearer token_guest"}

client = TestClient(app)


@pytest.fixture(autouse=True)
def clear_registry():
    registry = DeviceRegistry.get_instance()
    registry.clear()
    yield
    registry.clear()


# ---------------------------------------------------------------------------
# GET /api/devices/types (décorée avec @log_call)
# ---------------------------------------------------------------------------

class TestListDeviceTypes:
    def test_returns_success(self):
        response = client.get("/api/devices/types")
        assert response.status_code == 200

    def test_response_has_types_key(self):
        response = client.get("/api/devices/types")
        data = response.json()
        assert "types" in data
        assert "count" in data

    def test_metaclass_types_are_listed(self):
        response = client.get("/api/devices/types")
        types = response.json()["types"]
        assert "TemperatureSensor" in types
        assert "MotionDetector" in types

    def test_count_matches_types_length(self):
        response = client.get("/api/devices/types")
        data = response.json()
        assert data["count"] == len(data["types"])


# ---------------------------------------------------------------------------
# POST /api/devices/admin/create (@log_call + @require_role("admin") + @validate_input)
# ---------------------------------------------------------------------------

class TestAdminCreateDevice:
    def test_admin_can_create_device(self):
        payload = {
            "device_id": "d1",
            "name": "Admin Device",
            "room_name": "Office",
            "device_type": "light",
        }
        response = client.post(
            "/api/devices/admin/create", json=payload, headers=ADMIN_HEADERS
        )
        assert response.status_code == 200
        assert response.json()["status"] == "ok"

    def test_user_cannot_create_device_admin_endpoint(self):
        payload = {
            "device_id": "d2",
            "name": "User Device",
            "room_name": "Room",
            "device_type": "light",
        }
        response = client.post(
            "/api/devices/admin/create", json=payload, headers=USER_HEADERS
        )
        assert response.status_code == 403

    def test_guest_cannot_create_device_admin_endpoint(self):
        payload = {
            "device_id": "d3",
            "name": "Guest Device",
            "room_name": "Room",
            "device_type": "light",
        }
        response = client.post(
            "/api/devices/admin/create", json=payload, headers=GUEST_HEADERS
        )
        assert response.status_code == 403

    def test_no_token_returns_unauthorized(self):
        payload = {
            "device_id": "d4",
            "name": "No Token Device",
            "room_name": "Room",
            "device_type": "light",
        }
        response = client.post("/api/devices/admin/create", json=payload)
        assert response.status_code in (401, 403)

    def test_invalid_payload_returns_unprocessable(self):
        payload = {"name": "Missing Fields"}  # manque device_id, room_name, device_type
        response = client.post(
            "/api/devices/admin/create", json=payload, headers=ADMIN_HEADERS
        )
        assert response.status_code == 422

    def test_admin_create_returns_device_dict(self):
        payload = {
            "device_id": "d5",
            "name": "New Device",
            "room_name": "Kitchen",
            "device_type": "thermostat",
        }
        response = client.post(
            "/api/devices/admin/create", json=payload, headers=ADMIN_HEADERS
        )
        data = response.json()
        assert "device" in data
        assert data["device"]["device_id"] == "d5"


# ---------------------------------------------------------------------------
# GET /api/devices/admin/list (@log_call + @require_role("admin"))
# ---------------------------------------------------------------------------

class TestAdminListDevices:
    def test_admin_can_list_devices(self):
        response = client.get("/api/devices/admin/list", headers=ADMIN_HEADERS)
        assert response.status_code == 200
        data = response.json()
        assert "devices" in data
        assert "count" in data

    def test_user_blocked_from_admin_list(self):
        response = client.get("/api/devices/admin/list", headers=USER_HEADERS)
        assert response.status_code == 403

    def test_guest_blocked_from_admin_list(self):
        response = client.get("/api/devices/admin/list", headers=GUEST_HEADERS)
        assert response.status_code == 403

    def test_no_token_blocked_from_admin_list(self):
        response = client.get("/api/devices/admin/list")
        assert response.status_code in (401, 403)

    def test_admin_list_reflects_created_devices(self):
        payload = {
            "device_id": "list_test_1",
            "name": "Listed Device",
            "room_name": "Room",
            "device_type": "light",
        }
        client.post("/api/devices/admin/create", json=payload, headers=ADMIN_HEADERS)
        response = client.get("/api/devices/admin/list", headers=ADMIN_HEADERS)
        data = response.json()
        assert data["count"] >= 1
