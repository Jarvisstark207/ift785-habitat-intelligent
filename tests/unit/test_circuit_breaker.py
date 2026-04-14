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

