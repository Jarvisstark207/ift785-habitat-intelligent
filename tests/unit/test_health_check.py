"""
Tests unitaires — HealthService (Iteration 10)
"""

import pytest

from application.services.health_service import HealthService
from domain.resilience.circuit_breaker import (
    get_circuit_breaker,
    reset_all_circuit_breakers,
    CircuitBreakerState,
)
from app.core.metrics import get_metrics_collector


@pytest.fixture(autouse=True)
def setup():
    reset_all_circuit_breakers()
    get_metrics_collector().reset()
    yield
    reset_all_circuit_breakers()
    get_metrics_collector().reset()


class TestHealthServiceHealthy:
    def test_healthy_when_no_circuits(self):
        svc = HealthService()
        result = svc.check_health()
        assert result["status"] == "healthy"

    def test_healthy_has_services_key(self):
        svc = HealthService()
        result = svc.check_health()
        assert "services" in result

    def test_healthy_api_service_up(self):
        svc = HealthService()
        result = svc.check_health()
        assert result["services"]["api"]["healthy"] is True

    def test_healthy_when_circuit_closed(self):
        cb = get_circuit_breaker("test_api")
        assert cb.state == CircuitBreakerState.CLOSED
        svc = HealthService()
        result = svc.check_health()
        assert result["status"] == "healthy"


class TestHealthServiceDegraded:
    def test_degraded_when_circuit_open(self):
        cb = get_circuit_breaker("philips_hue")
        cb.force_open()
        svc = HealthService()
        result = svc.check_health()
        assert result["status"] == "degraded"

    def test_circuit_status_in_services(self):
        cb = get_circuit_breaker("weather_api")
        cb.force_open()
        svc = HealthService()
        result = svc.check_health()
        cb_statuses = result["services"]["circuit_breakers"]
        assert "weather_api" in cb_statuses
        assert cb_statuses["weather_api"]["healthy"] is False


class TestReadinessCheck:
    def test_ready_when_healthy(self):
        svc = HealthService()
        result = svc.check_readiness()
        assert "ready" in result

    def test_not_ready_when_circuit_open(self):
        cb = get_circuit_breaker("external_service")
        cb.force_open()
        svc = HealthService()
        result = svc.check_readiness()
        assert result["ready"] is False

    def test_ready_true_when_all_closed(self):
        cb = get_circuit_breaker("my_service")
        cb.force_closed()
        svc = HealthService()
        result = svc.check_readiness()
        assert result["ready"] is True


class TestMetricsSummary:
    def test_metrics_summary_has_requests_total(self):
        svc = HealthService()
        metrics = svc.get_metrics_summary()
        assert "requests_total" in metrics

    def test_metrics_summary_has_circuit_breakers(self):
        get_circuit_breaker("cb_test")
        svc = HealthService()
        metrics = svc.get_metrics_summary()
        assert "circuit_breakers" in metrics

    def test_open_circuits_count(self):
        cb = get_circuit_breaker("open_cb")
        cb.force_open()
        svc = HealthService()
        metrics = svc.get_metrics_summary()
        assert metrics["open_circuits"] >= 1
