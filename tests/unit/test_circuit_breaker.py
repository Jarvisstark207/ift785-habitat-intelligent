"""
Tests unitaires — CircuitBreaker (Iteration 10 : Resilience)

Couvre :
  - Etat initial CLOSED
  - Passage CLOSED -> OPEN apres failure_threshold echecs
  - Passage OPEN -> HALF_OPEN apres recovery_timeout
  - Passage HALF_OPEN -> CLOSED apres succes
  - Passage HALF_OPEN -> OPEN apres echec
  - force_open / force_closed / reset
  - CircuitOpenError
  - get_stats
  - Registry global
"""

import time
import pytest

from domain.resilience.circuit_breaker import (
    CircuitBreaker,
    CircuitBreakerState,
    CircuitOpenError,
    State,
    get_circuit_breaker,
    get_all_circuit_breakers,
    reset_all_circuit_breakers,
)


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture(autouse=True)
def clean_registry():
    """Nettoie le registre global avant chaque test."""
    reset_all_circuit_breakers()
    yield
    reset_all_circuit_breakers()


def failing():
    raise RuntimeError("service down")


def succeeding():
    return "ok"


# ---------------------------------------------------------------------------
# Etat initial
# ---------------------------------------------------------------------------

class TestCircuitBreakerInitial:
    def test_initial_state_is_closed(self):
        cb = CircuitBreaker()
        assert cb.state == CircuitBreakerState.CLOSED

    def test_state_enum_alias(self):
        assert State.CLOSED == CircuitBreakerState.CLOSED
        assert State.OPEN == CircuitBreakerState.OPEN
        assert State.HALF_OPEN == CircuitBreakerState.HALF_OPEN

    def test_default_threshold(self):
        cb = CircuitBreaker()
        assert cb.failure_threshold == 3

    def test_custom_threshold(self):
        cb = CircuitBreaker(failure_threshold=5)
        assert cb.failure_threshold == 5

    def test_success_passes_through(self):
        cb = CircuitBreaker()
        result = cb.call(succeeding)
        assert result == "ok"

    def test_failure_count_starts_at_zero(self):
        cb = CircuitBreaker()
        assert cb._failure_count == 0


# ---------------------------------------------------------------------------
# Transition CLOSED -> OPEN
# ---------------------------------------------------------------------------

class TestCircuitBreakerOpens:
    def test_opens_after_threshold(self):
        cb = CircuitBreaker(failure_threshold=3)
        for _ in range(3):
            with pytest.raises(RuntimeError):
                cb.call(failing)
        assert cb.state == CircuitBreakerState.OPEN

    def test_opens_after_threshold_v2(self):
        cb = CircuitBreaker(failure_threshold=3)
        for _ in range(3):
            with pytest.raises(Exception):
                cb.call(lambda: (_ for _ in ()).throw(RuntimeError("fail")))
        assert cb.state == State.OPEN

    def test_not_open_before_threshold(self):
        cb = CircuitBreaker(failure_threshold=3)
        for _ in range(2):
            with pytest.raises(RuntimeError):
                cb.call(failing)
        assert cb.state == CircuitBreakerState.CLOSED

    def test_raises_circuit_open_error_when_open(self):
        cb = CircuitBreaker(failure_threshold=1)
        with pytest.raises(RuntimeError):
            cb.call(failing)
        assert cb.state == CircuitBreakerState.OPEN
        with pytest.raises(CircuitOpenError):
            cb.call(succeeding)

    def test_circuit_open_error_message(self):
        cb = CircuitBreaker(name="philips", failure_threshold=1)
        with pytest.raises(RuntimeError):
            cb.call(failing)
        with pytest.raises(CircuitOpenError, match="philips"):
            cb.call(succeeding)

    def test_success_resets_failure_count(self):
        cb = CircuitBreaker(failure_threshold=3)
        with pytest.raises(RuntimeError):
            cb.call(failing)
        cb.call(succeeding)
        assert cb._failure_count == 0


# ---------------------------------------------------------------------------
# Transition OPEN -> HALF_OPEN -> CLOSED / OPEN
# ---------------------------------------------------------------------------

class TestCircuitBreakerHalfOpen:
    def test_half_open_after_timeout(self):
        cb = CircuitBreaker(failure_threshold=1, recovery_timeout=0.05)
        with pytest.raises(RuntimeError):
            cb.call(failing)
        assert cb.state == CircuitBreakerState.OPEN
        time.sleep(0.1)
        assert cb.state == CircuitBreakerState.HALF_OPEN

    def test_half_open_to_closed_on_success(self):
        cb = CircuitBreaker(failure_threshold=1, recovery_timeout=0.05)
        with pytest.raises(RuntimeError):
            cb.call(failing)
        time.sleep(0.1)
        result = cb.call(succeeding)
        assert result == "ok"
        assert cb.state == CircuitBreakerState.CLOSED

    def test_half_open_to_open_on_failure(self):
        cb = CircuitBreaker(failure_threshold=1, recovery_timeout=0.05)
        with pytest.raises(RuntimeError):
            cb.call(failing)
        time.sleep(0.1)
        assert cb.state == CircuitBreakerState.HALF_OPEN
        with pytest.raises(RuntimeError):
            cb.call(failing)
        assert cb.state == CircuitBreakerState.OPEN


# ---------------------------------------------------------------------------
# force_open / force_closed / reset
# ---------------------------------------------------------------------------

class TestCircuitBreakerForce:
    def test_force_open(self):
        cb = CircuitBreaker()
        cb.force_open()
        assert cb.state == CircuitBreakerState.OPEN

    def test_force_open_rejects_calls(self):
        cb = CircuitBreaker()
        cb.force_open()
        with pytest.raises(CircuitOpenError):
            cb.call(succeeding)

    def test_force_closed(self):
        cb = CircuitBreaker(failure_threshold=1)
        with pytest.raises(RuntimeError):
            cb.call(failing)
        assert cb.state == CircuitBreakerState.OPEN
        cb.force_closed()
        assert cb.state == CircuitBreakerState.CLOSED

    def test_reset(self):
        cb = CircuitBreaker(failure_threshold=1)
        with pytest.raises(RuntimeError):
            cb.call(failing)
        cb.reset()
        assert cb.state == CircuitBreakerState.CLOSED
        assert cb._failure_count == 0
        assert cb._total_calls == 0


# ---------------------------------------------------------------------------
# get_stats
# ---------------------------------------------------------------------------

class TestCircuitBreakerStats:
    def test_get_stats_keys(self):
        cb = CircuitBreaker(name="test_cb")
        stats = cb.get_stats()
        assert "name" in stats
        assert "state" in stats
        assert "failure_count" in stats
        assert "total_calls" in stats

    def test_stats_state_value(self):
        cb = CircuitBreaker()
        assert cb.get_stats()["state"] == "closed"


# ---------------------------------------------------------------------------
# Registry global
# ---------------------------------------------------------------------------

class TestCircuitBreakerRegistry:
    def test_get_circuit_breaker_creates(self):
        cb = get_circuit_breaker("weather_api")
        assert cb.name == "weather_api"

    def test_get_circuit_breaker_singleton(self):
        cb1 = get_circuit_breaker("sensor_api")
        cb2 = get_circuit_breaker("sensor_api")
        assert cb1 is cb2

    def test_get_all_circuit_breakers(self):
        get_circuit_breaker("service_a")
        get_circuit_breaker("service_b")
        all_cb = get_all_circuit_breakers()
        assert "service_a" in all_cb
        assert "service_b" in all_cb
