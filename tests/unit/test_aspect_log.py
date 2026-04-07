"""
Tests unitaires - @aspect_log (Itération 9 : AOP)
"""

import asyncio
import logging
import pytest

from app.core.aspects import aspect_log


def run(coro):
    return asyncio.get_event_loop().run_until_complete(coro)


# ---------------------------------------------------------------------------
# Fonctionnement de base
# ---------------------------------------------------------------------------

class TestAspectLogBasic:
    def test_sync_returns_value(self):
        @aspect_log()
        def add(a, b):
            return a + b
        assert add(2, 3) == 5

    def test_async_returns_value(self):
        @aspect_log()
        async def fetch():
            return 42
        assert run(fetch()) == 42

    def test_preserves_function_name_sync(self):
        @aspect_log()
        def my_func():
            pass
        assert my_func.__name__ == "my_func"

    def test_preserves_function_name_async(self):
        @aspect_log()
        async def my_async():
            pass
        assert my_async.__name__ == "my_async"

    def test_preserves_docstring(self):
        @aspect_log()
        def documented():
            """My doc."""
        assert documented.__doc__ == "My doc."

    def test_passes_args(self):
        @aspect_log()
        def multiply(x, y):
            return x * y
        assert multiply(3, 4) == 12

    def test_passes_kwargs(self):
        @aspect_log()
        def greet(name="World"):
            return f"Hello {name}"
        assert greet(name="Bob") == "Hello Bob"

    def test_sync_propagates_exception(self):
        @aspect_log()
        def boom():
            raise ValueError("fail")
        with pytest.raises(ValueError, match="fail"):
            boom()

    def test_async_propagates_exception(self):
        @aspect_log()
        async def async_boom():
            raise RuntimeError("async fail")
        with pytest.raises(RuntimeError, match="async fail"):
            run(async_boom())

