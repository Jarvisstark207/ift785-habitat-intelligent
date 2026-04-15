"""
Tests d'integration — Transitions completes Circuit Breaker (Iteration 10)

Verifie les cycles CLOSED -> OPEN -> HALF_OPEN -> CLOSED/OPEN
avec des scenarios realistes (appel de service externe simule).
"""

import time
import pytest

from domain.resilience.circuit_breaker import (
    CircuitBreaker,
    CircuitBreakerState,
    CircuitOpenError,
    get_circuit_breaker,
    reset_all_circuit_breakers,
)


@pytest.fixture(autouse=True)
def clean():
    reset_all_circuit_breakers()
    yield
    reset_all_circuit_breakers()


class TestFullCycleClosedOpenHalfOpen:
    def test_full_cycle_closed_open_half_open_closed(self):
        """Cycle complet CLOSED -> OPEN -> HALF_OPEN -> CLOSED."""
        cb = CircuitBreaker(
            name="philips_hue",
            failure_threshold=3,
            recovery_timeout=0.05,
        )

        # Phase CLOSED : appels normaux
        assert cb.state == CircuitBreakerState.CLOSED
        cb.call(lambda: "ok")
        assert cb.state == CircuitBreakerState.CLOSED

        # Phase OPEN : 3 echecs consecutifs
        for _ in range(3):
            with pytest.raises(RuntimeError):
                cb.call(lambda: (_ for _ in ()).throw(RuntimeError("fail")))
        assert cb.state == CircuitBreakerState.OPEN

        # Phase OPEN : appels rejetes immediatement
        with pytest.raises(CircuitOpenError):
            cb.call(lambda: "ok")

        # Phase HALF_OPEN : apres recovery_timeout
        time.sleep(0.1)
        assert cb.state == CircuitBreakerState.HALF_OPEN

        # Appel de test reussi -> retour CLOSED
        cb.call(lambda: "recovered")
        assert cb.state == CircuitBreakerState.CLOSED

    def test_full_cycle_half_open_back_to_open_on_failure(self):
        """HALF_OPEN -> OPEN si le test echoue."""
        cb = CircuitBreaker(
            name="weather_api",
            failure_threshold=1,
            recovery_timeout=0.05,
        )

        with pytest.raises(RuntimeError):
            cb.call(lambda: (_ for _ in ()).throw(RuntimeError("down")))
        assert cb.state == CircuitBreakerState.OPEN

        time.sleep(0.1)
        assert cb.state == CircuitBreakerState.HALF_OPEN

        with pytest.raises(RuntimeError):
            cb.call(lambda: (_ for _ in ()).throw(RuntimeError("still down")))
        assert cb.state == CircuitBreakerState.OPEN

    def test_multiple_circuits_isolated(self):
        """Chaque service a son propre circuit (Bulkhead)."""
        cb_a = get_circuit_breaker("service_a", failure_threshold=2)
        cb_b = get_circuit_breaker("service_b", failure_threshold=2)

        # Faire echouer service_a
        for _ in range(2):
            with pytest.raises(RuntimeError):
                cb_a.call(lambda: (_ for _ in ()).throw(RuntimeError()))

        assert cb_a.state == CircuitBreakerState.OPEN
        assert cb_b.state == CircuitBreakerState.CLOSED

    def test_circuit_recovers_multiple_times(self):
        """Un circuit peut s'ouvrir et se fermer plusieurs fois."""
        cb = CircuitBreaker(failure_threshold=1, recovery_timeout=0.05)

        for cycle in range(3):
            # Ouvrir
            with pytest.raises(RuntimeError):
                cb.call(lambda: (_ for _ in ()).throw(RuntimeError()))
            assert cb.state == CircuitBreakerState.OPEN

            # Attendre + recuperer
            time.sleep(0.1)
            cb.call(lambda: "ok")
            assert cb.state == CircuitBreakerState.CLOSED

    def test_success_resets_failure_counter_between_failures(self):
        """Un succes remet le compteur d'echecs a zero."""
        cb = CircuitBreaker(failure_threshold=3)

        # 2 echecs
        for _ in range(2):
            with pytest.raises(RuntimeError):
                cb.call(lambda: (_ for _ in ()).throw(RuntimeError()))

        # Succes -> compteur remis a zero
        cb.call(lambda: "ok")
        assert cb._failure_count == 0

        # 2 echecs supplementaires ne doivent pas ouvrir
        for _ in range(2):
            with pytest.raises(RuntimeError):
                cb.call(lambda: (_ for _ in ()).throw(RuntimeError()))
        assert cb.state == CircuitBreakerState.CLOSED
