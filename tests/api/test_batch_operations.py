"""
Tests API pour les endpoints batch et transactions - Iteration 6
"""

import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock
from infrastructure.db.sqlalchemy_models import DeviceRecord


@pytest.fixture
def client():
    from app import app
    return TestClient(app)


class TestBatchDevicesEndpoint:
    def test_batch_create_success(self, client):
        devices = [
            {"device_id": "api-b1", "name": "API Batch 1", "device_type": "light"},
            {"device_id": "api-b2", "name": "API Batch 2", "device_type": "sensor"},
        ]
        response = client.post("/api/devices/batch", json=devices)
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "ok"
        assert data["created"] == 2
        assert "api-b1" in data["device_ids"]
        assert "api-b2" in data["device_ids"]

    def test_batch_create_single_device(self, client):
        devices = [{"device_id": "api-single", "name": "Single Device"}]
        response = client.post("/api/devices/batch", json=devices)
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "ok"
        assert data["created"] == 1

    def test_batch_create_missing_name_rolls_back(self, client):
        devices = [
            {"device_id": "api-valid", "name": "Valid"},
            {"device_id": "api-invalid"},
        ]
        response = client.post("/api/devices/batch", json=devices)
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "error"
        assert data["rolled_back"] is True

    def test_batch_create_missing_device_id_rolls_back(self, client):
        devices = [{"name": "No ID Device"}]
        response = client.post("/api/devices/batch", json=devices)
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "error"
        assert data["rolled_back"] is True

    def test_batch_create_empty_list(self, client):
        response = client.post("/api/devices/batch", json=[])
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "ok"
        assert data["created"] == 0

    def test_batch_create_with_all_fields(self, client):
        devices = [{
            "device_id": "api-full",
            "name": "Full Device",
            "room_name": "salon",
            "device_type": "thermostat",
            "manufacturer": "Nest",
            "status": "active",
        }]
        response = client.post("/api/devices/batch", json=devices)
        assert response.status_code == 200
        assert response.json()["status"] == "ok"


class TestRollbackTestEndpoint:
    def test_rollback_test_default_force_rollback(self, client):
        response = client.post("/api/transactions/rollback-test", json={})
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "ok"
        assert data["action"] == "rollback"
        assert data["persisted"] is False

    def test_rollback_test_force_rollback_true(self, client):
        response = client.post(
            "/api/transactions/rollback-test",
            json={"force_rollback": True}
        )
        assert response.status_code == 200
        data = response.json()
        assert data["action"] == "rollback"
        assert data["persisted"] is False
        assert "attempted_inserts" in data

    def test_rollback_test_force_rollback_false(self, client):
        response = client.post(
            "/api/transactions/rollback-test",
            json={"force_rollback": False}
        )
        assert response.status_code == 200
        data = response.json()
        assert data["action"] == "commit"
        assert data["persisted"] is True

    def test_rollback_test_no_body(self, client):
        response = client.post("/api/transactions/rollback-test")
        assert response.status_code == 200

    def test_rollback_test_custom_devices(self, client):
        response = client.post(
            "/api/transactions/rollback-test",
            json={
                "force_rollback": True,
                "devices": [
                    {"device_id": "custom-1", "name": "Custom 1"},
                    {"device_id": "custom-2", "name": "Custom 2"},
                ]
            }
        )
        assert response.status_code == 200
        data = response.json()
        assert data["persisted"] is False
        assert len(data["attempted_inserts"]) == 2
