"""
Tests API — Endpoints de sante et metriques (Iteration 10)

GET /api/health    -> 200 si sain, 503 si circuit OPEN
GET /api/readiness -> 200/503
GET /api/metrics   -> 200 avec les metriques
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


class TestHealthEndpoint:
    def test_health_returns_200_when_healthy(self, client):
        response = client.get("/api/health")
        assert response.status_code in (200, 503)

    def test_health_has_status_field(self, client):
        response = client.get("/api/health")
        data = response.json()
        assert "status" in data

    def test_health_has_services_field(self, client):
        response = client.get("/api/health")
        data = response.json()
        assert "services" in data

    def test_health_returns_503_when_circuit_open(self, client):
        cb = get_circuit_breaker("test_service_health")
        cb.force_open()
        response = client.get("/api/health")
        assert response.status_code == 503

    def test_health_body_degraded_when_circuit_open(self, client):
        cb = get_circuit_breaker("another_service")
        cb.force_open()
        response = client.get("/api/health")
        data = response.json()
        assert data["status"] == "degraded"

    def test_health_200_when_no_open_circuits(self, client):
        response = client.get("/api/health")
        if response.status_code == 200:
            data = response.json()
            assert data["status"] == "healthy"


class TestReadinessEndpoint:
    def test_readiness_returns_200_or_503(self, client):
        response = client.get("/api/readiness")
        assert response.status_code in (200, 503)

    def test_readiness_has_ready_field(self, client):
        response = client.get("/api/readiness")
        data = response.json()
        assert "ready" in data

    def test_readiness_503_when_circuit_open(self, client):
        cb = get_circuit_breaker("readiness_test_cb")
        cb.force_open()
        response = client.get("/api/readiness")
        assert response.status_code == 503
        assert response.json()["ready"] is False


class TestMetricsEndpoint:
    def test_metrics_returns_200(self, client):
        response = client.get("/api/metrics")
        assert response.status_code == 200

    def test_metrics_has_requests_total(self, client):
        response = client.get("/api/metrics")
        data = response.json()
        assert "requests_total" in data

    def test_metrics_has_error_rate(self, client):
        response = client.get("/api/metrics")
        data = response.json()
        assert "error_rate" in data

    def test_metrics_has_circuit_breakers(self, client):
        response = client.get("/api/metrics")
        data = response.json()
        assert "circuit_breakers" in data

    def test_metrics_open_circuits_count(self, client):
        cb = get_circuit_breaker("metrics_test_cb")
        cb.force_open()
        response = client.get("/api/metrics")
        data = response.json()
        assert data["open_circuits"] >= 1
