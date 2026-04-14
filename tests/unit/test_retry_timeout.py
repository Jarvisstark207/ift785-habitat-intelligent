"""
Tests unitaires - @timeout + interaction @aspect_retry + CircuitBreaker
"""

import time
import pytest

from domain.resilience.timeout import timeout
from domain.resilience.circuit_breaker import (
    CircuitBreaker,
    CircuitOpenError,
    reset_all_circuit_breakers,
)
from app.core.aspects import aspect_retry


# ---------------------------------------------------------------------------
# Fixture
# ---------------------------------------------------------------------------

@pytest.fixture(autouse=True)
def clean_cbs():
    reset_all_circuit_breakers()
    yield
    reset_all_circuit_breakers()


# ---------------------------------------------------------------------------
# @timeout
# ---------------------------------------------------------------------------

class TestTimeout:
    def test_timeout_passes_when_fast(self):
        @timeout(seconds=1.0)
        def fast():
            return "done"

        assert fast() == "done"

    def test_timeout_raises_when_slow(self):
        @timeout(seconds=0.05)
        def slow():
            time.sleep(0.2)
            return "never"

        with pytest.raises(TimeoutError):
            slow()

    def test_timeout_preserves_return_value(self):
        @timeout(seconds=1.0)
        def compute():
            return 42

        assert compute() == 42

    def test_timeout_preserves_function_name(self):
        @timeout(seconds=1.0)
        def my_function():
            pass

        assert my_function.__name__ == "my_function"

    def test_timeout_propagates_exception(self):
        @timeout(seconds=1.0)
        def broken():
            raise ValueError("boom")

        with pytest.raises(ValueError, match="boom"):
            broken()

    def test_timeout_with_args(self):
        @timeout(seconds=1.0)
        def add(a, b):
            return a + b

        assert add(3, 4) == 7

    def test_timeout_error_message_contains_function_name(self):
        @timeout(seconds=0.05)
        def slow_api_call():
            time.sleep(1)

        with pytest.raises(TimeoutError, match="slow_api_call"):
            slow_api_call()


# ---------------------------------------------------------------------------
# Interaction aspect_retry + CircuitBreaker
# ---------------------------------------------------------------------------

class TestRetryWithCircuitBreaker:
    def test_retry_exhaustion_triggers_circuit_breaker(self):
        """Apres retry exhaustion, le CB comptabilise les echecs."""
        cb = CircuitBreaker(failure_threshold=3, recovery_timeout=60)
        attempts = [0]

        def flaky():
            attempts[0] += 1
            raise RuntimeError("fail")

        @aspect_retry(max_attempts=3, backoff=0)
        def protected():
            return cb.call(flaky)

        with pytest.raises(RuntimeError):
            protected()

        assert cb._failure_count == 3
        assert cb.state.value == "open"

    def test_circuit_open_stops_retries(self):
        """Quand le CB est OPEN, il leve CircuitOpenError sans retry."""
        cb = CircuitBreaker(failure_threshold=1)
        cb.force_open()
        call_count = [0]

        @aspect_retry(max_attempts=3, backoff=0)
        def protected():
            call_count[0] += 1
            return cb.call(lambda: "ok")

        with pytest.raises(CircuitOpenError):
            protected()

    def test_retry_succeeds_before_circuit_opens(self):
        """Si le retry finit par reussir, le CB reste CLOSED."""
        cb = CircuitBreaker(failure_threshold=5)
        attempts = [0]

        def eventually_works():
            attempts[0] += 1
            if attempts[0] < 3:
                raise RuntimeError("not yet")
            return "success"

        @aspect_retry(max_attempts=5, backoff=0)
        def protected():
            return cb.call(eventually_works)

        result = protected()
        assert result == "success"
        assert cb.state.value == "closed"
