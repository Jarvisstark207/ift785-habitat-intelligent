"""
Tests API - Stack complete + integration Circuit Breaker / Health (Iter 10)
"""

import pytest
from fastapi.testclient import TestClient

from domain.resilience.circuit_breaker import (
    get_circuit_breaker,
    reset_all_circuit_breakers,
)
from app.core.metrics import get_metrics_collector


@pytest.fixture
def client():
    from app import app
    return TestClient(app, raise_server_exceptions=False)


@pytest.fixture(autouse=True)
def clean():
    reset_all_circuit_breakers()
    get_metrics_collector().reset()
    yield
    reset_all_circuit_breakers()
    get_metrics_collector().reset()


class TestFullStackHealth:
    def test_app_starts_successfully(self, client):
        """L'application demarre et repond aux requetes."""
        response = client.get("/api/health")
        assert response.status_code in (200, 503)

    def test_health_check_reflects_circuit_state(self, client):
        """L'etat du CB est reflete dans /api/health."""
        cb = get_circuit_breaker("stack_test_cb")

        # CB ferme -> health peut etre healthy
        client.get("/api/health")

        # Ouvrir le CB
        cb.force_open()
        response = client.get("/api/health")
        assert response.json()["status"] == "degraded"

        # Refermer le CB
        cb.force_closed()
        response = client.get("/api/health")
        # Peut rester healthy si la DB est ok
        assert response.json()["status"] in ("healthy", "degraded")

    def test_readiness_consistent_with_health(self, client):
        """Readiness et health sont coherents."""
        cb = get_circuit_breaker("readiness_stack_cb")
        cb.force_open()

        health = client.get("/api/health").json()
        readiness = client.get("/api/readiness").json()

        assert health["status"] == "degraded"
        assert readiness["ready"] is False

    def test_metrics_endpoint_accessible(self, client):
        """Les metriques sont accessibles."""
        response = client.get("/api/metrics")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data["requests_total"], int)

    def test_existing_endpoints_still_work(self, client):
        """Les endpoints precedents (iter 1-9) ne sont pas casses."""
        response = client.get("/api/sensors/latest")
        assert response.status_code in (200, 404, 422)

    def test_circuit_breaker_in_metrics_when_open(self, client):
        """Un CB ouvert apparait dans les metriques."""
        cb = get_circuit_breaker("full_stack_open_cb")
        cb.force_open()

        response = client.get("/api/metrics")
        data = response.json()
        assert data["open_circuits"] >= 1

        cb_names = [c["name"] for c in data["circuit_breakers"]]
        assert "full_stack_open_cb" in cb_names
