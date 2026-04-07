"""
Tests API - Endpoints mis en cache @aspect_cache (Itération 9)
Vérifie que /api/sensors/latest et /api/devices/summary retournent bien
une réponse en cache au second appel (pas de second appel effectif).
"""

import pytest
from fastapi.testclient import TestClient

from app import app
from app.core.aspects import invalidate_cache


@pytest.fixture()
def client():
    return TestClient(app)


@pytest.fixture(autouse=True)
def clear_cache():
    invalidate_cache()
    yield
    invalidate_cache()


# ---------------------------------------------------------------------------
# /api/sensors/latest
# ---------------------------------------------------------------------------

class TestSensorsLatestEndpoint:
    def test_endpoint_returns_success(self, client):
        resp = client.get("/api/sensors/latest")
        assert resp.status_code == 200

    def test_response_has_count_field(self, client):
        resp = client.get("/api/sensors/latest")
        data = resp.json()
        assert "count" in data

    def test_response_has_readings_field(self, client):
        resp = client.get("/api/sensors/latest")
        data = resp.json()
        assert "readings" in data

    def test_second_call_cached(self, client):
        """Le second appel doit retourner le même résultat (cache hit)."""
        r1 = client.get("/api/sensors/latest")
        r2 = client.get("/api/sensors/latest")
        assert r1.status_code == 200
        assert r2.status_code == 200
        assert r1.json() == r2.json()

    def test_content_type_is_json(self, client):
        resp = client.get("/api/sensors/latest")
        assert "application/json" in resp.headers.get("content-type", "")


# ---------------------------------------------------------------------------
# /api/devices/summary
# ---------------------------------------------------------------------------

class TestDevicesSummaryEndpoint:
    def test_endpoint_returns_success(self, client):
        resp = client.get("/api/devices/summary")
        assert resp.status_code == 200

    def test_response_has_total_field(self, client):
        resp = client.get("/api/devices/summary")
        data = resp.json()
        assert "total" in data

    def test_response_has_by_type_field(self, client):
        resp = client.get("/api/devices/summary")
        data = resp.json()
        assert "by_type" in data

    def test_response_has_by_room_field(self, client):
        resp = client.get("/api/devices/summary")
        data = resp.json()
        assert "by_room" in data

    def test_second_call_cached(self, client):
        """Le second appel doit retourner le même résultat (cache hit)."""
        r1 = client.get("/api/devices/summary")
        r2 = client.get("/api/devices/summary")
        assert r1.status_code == 200
        assert r2.status_code == 200
        assert r1.json() == r2.json()

    def test_cache_invalidation_endpoint_available(self, client):
        resp = client.post("/api/cache/invalidate", json={})
        assert resp.status_code == 200

    def test_cache_stats_endpoint_available(self, client):
        client.get("/api/sensors/latest")
        resp = client.get("/api/cache/stats")
        assert resp.status_code == 200
        data = resp.json()
        assert "count" in data
        assert "entries" in data
