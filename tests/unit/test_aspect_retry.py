"""
Tests unitaires - @aspect_retry (Itération 9 : AOP)
"""

import asyncio
import pytest

from app.core.aspects import aspect_retry


def run(coro):
    return asyncio.get_event_loop().run_until_complete(coro)


# ---------------------------------------------------------------------------
# Fonctionnement de base
# ---------------------------------------------------------------------------

class TestAspectRetryBasic:
    def test_sync_succeeds_first_try(self):
        @aspect_retry(max_attempts=3, backoff=0)
        def succeed():
            return "ok"
        assert succeed() == "ok"

    def test_async_succeeds_first_try(self):
        @aspect_retry(max_attempts=3, backoff=0)
        async def succeed():
            return "ok"
        assert run(succeed()) == "ok"

    def test_preserves_function_name(self):
        @aspect_retry(max_attempts=3, backoff=0)
        def my_func():
            pass
        assert my_func.__name__ == "my_func"

    def test_preserves_docstring(self):
        @aspect_retry(max_attempts=3, backoff=0)
        def documented():
            """My doc."""
        assert documented.__doc__ == "My doc."

    def test_sync_retries_on_failure_then_succeeds(self):
        attempts = [0]

        @aspect_retry(max_attempts=3, backoff=0)
        def flaky():
            attempts[0] += 1
            if attempts[0] < 3:
                raise RuntimeError("not yet")
            return "done"

        result = flaky()
        assert result == "done"
        assert attempts[0] == 3

    def test_async_retries_on_failure_then_succeeds(self):
        attempts = [0]

        @aspect_retry(max_attempts=3, backoff=0)
        async def flaky():
            attempts[0] += 1
            if attempts[0] < 2:
                raise RuntimeError("not yet")
            return "done"

        result = run(flaky())
        assert result == "done"
        assert attempts[0] == 2

    def test_raises_after_max_attempts(self):
        @aspect_retry(max_attempts=2, backoff=0)
        def always_fail():
            raise ValueError("always fail")

        with pytest.raises(ValueError, match="always fail"):
            always_fail()

    def test_async_raises_after_max_attempts(self):
        @aspect_retry(max_attempts=2, backoff=0)
        async def always_fail():
            raise RuntimeError("always fail")

        with pytest.raises(RuntimeError):
            run(always_fail())

    def test_attempt_count_matches_max_attempts(self):
        attempts = [0]

        @aspect_retry(max_attempts=4, backoff=0)
        def count_attempts():
            attempts[0] += 1
            raise RuntimeError("fail")

        with pytest.raises(RuntimeError):
            count_attempts()
        assert attempts[0] == 4


# ---------------------------------------------------------------------------
# Sélection des exceptions
# ---------------------------------------------------------------------------

class TestAspectRetryExceptions:
    def test_only_retries_specified_exceptions(self):
        attempts = [0]

        @aspect_retry(max_attempts=3, backoff=0, exceptions=(ValueError,))
        def raise_value_error():
            attempts[0] += 1
            raise ValueError("v")

        with pytest.raises(ValueError):
            raise_value_error()
        assert attempts[0] == 3

    def test_does_not_retry_unspecified_exceptions(self):
        attempts = [0]

        @aspect_retry(max_attempts=3, backoff=0, exceptions=(ValueError,))
        def raise_runtime_error():
            attempts[0] += 1
            raise RuntimeError("not retried")

        with pytest.raises(RuntimeError):
            raise_runtime_error()
        assert attempts[0] == 1

    def test_multiple_exception_types(self):
        attempts = [0]
        errors = [TypeError("t"), ValueError("v"), RuntimeError("r")]

        @aspect_retry(max_attempts=3, backoff=0, exceptions=(TypeError, ValueError))
        def flaky():
            exc = errors[attempts[0]]
            attempts[0] += 1
            raise exc

        with pytest.raises(RuntimeError):
            flaky()
        assert attempts[0] == 3


# ---------------------------------------------------------------------------
# Backoff
# ---------------------------------------------------------------------------

class TestAspectRetryBackoff:
    def test_backoff_parameter_accepted(self):
        @aspect_retry(max_attempts=1, backoff=1.0)
        def succeed():
            return "ok"
        assert succeed() == "ok"

    def test_max_attempts_one_no_retry(self):
        attempts = [0]

        @aspect_retry(max_attempts=1, backoff=0)
        def always_fail():
            attempts[0] += 1
            raise RuntimeError("fail")

        with pytest.raises(RuntimeError):
            always_fail()
        assert attempts[0] == 1
