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

