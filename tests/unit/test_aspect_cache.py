"""
Tests unitaires - @aspect_cache (Itération 9 : AOP)
"""

import asyncio
import time
import pytest

from app.core.aspects import aspect_cache, invalidate_cache, get_cache_store, _cache_store


def run(coro):
    return asyncio.get_event_loop().run_until_complete(coro)


@pytest.fixture(autouse=True)
def clear_cache():
    """Vide le cache avant chaque test."""
    invalidate_cache()
    yield
    invalidate_cache()


# ---------------------------------------------------------------------------
# Comportement de base
# ---------------------------------------------------------------------------

class TestAspectCacheBasic:
    def test_sync_returns_value(self):
        @aspect_cache(ttl=60)
        def compute():
            return 42
        assert compute() == 42

    def test_async_returns_value(self):
        @aspect_cache(ttl=60)
        async def fetch():
            return 99
        assert run(fetch()) == 99

    def test_preserves_function_name(self):
        @aspect_cache(ttl=60)
        def my_func():
            pass
        assert my_func.__name__ == "my_func"

    def test_preserves_docstring(self):
        @aspect_cache(ttl=60)
        def documented():
            """My doc."""
        assert documented.__doc__ == "My doc."

    def test_sync_second_call_uses_cache(self):
        call_count = [0]

        @aspect_cache(ttl=60)
        def expensive():
            call_count[0] += 1
            return call_count[0]

        first = expensive()
        second = expensive()
        assert first == second == 1
        assert call_count[0] == 1

    def test_async_second_call_uses_cache(self):
        call_count = [0]

        @aspect_cache(ttl=60)
        async def expensive():
            call_count[0] += 1
            return call_count[0]

        first = run(expensive())
        second = run(expensive())
        assert first == second == 1
        assert call_count[0] == 1

    def test_different_args_different_cache_entries(self):
        call_count = [0]

        @aspect_cache(ttl=60)
        def compute(x):
            call_count[0] += 1
            return x * 2

        assert compute(1) == 2
        assert compute(2) == 4
        assert call_count[0] == 2

    def test_cache_miss_after_ttl_expiry(self):
        call_count = [0]

        @aspect_cache(ttl=0.05)
        def compute():
            call_count[0] += 1
            return call_count[0]

        compute()
        time.sleep(0.1)
        compute()
        assert call_count[0] == 2


# ---------------------------------------------------------------------------
# Clé personnalisée (key_fn)
# ---------------------------------------------------------------------------

class TestAspectCacheKeyFn:
    def test_key_fn_used(self):
        call_count = [0]

        @aspect_cache(ttl=60, key_fn=lambda x: f"custom:{x}")
        def compute(x):
            call_count[0] += 1
            return x

        compute(5)
        compute(5)
        assert call_count[0] == 1

    def test_different_key_fn_results_different_entries(self):
        call_count = [0]

        @aspect_cache(ttl=60, key_fn=lambda x: f"k:{x}")
        def compute(x):
            call_count[0] += 1
            return x

        compute(1)
        compute(2)
        assert call_count[0] == 2


# ---------------------------------------------------------------------------
# Invalidation
# ---------------------------------------------------------------------------

class TestAspectCacheInvalidation:
    def test_invalidate_all(self):
        @aspect_cache(ttl=60)
        def f():
            return 1

        f()
        count = invalidate_cache()
        assert count >= 1
        assert len(_cache_store) == 0

    def test_invalidate_by_prefix(self):
        @aspect_cache(ttl=60, key_fn=lambda: "prefix:key1")
        def f1():
            return 1

        @aspect_cache(ttl=60, key_fn=lambda: "other:key2")
        def f2():
            return 2

        f1()
        f2()
        invalidate_cache(prefix="prefix:")
        store = get_cache_store()
        assert all(not k.startswith("prefix:") for k in store)

    def test_get_cache_store_returns_ttl(self):
        @aspect_cache(ttl=60, key_fn=lambda: "test:ttl")
        def f():
            return "x"

        f()
        store = get_cache_store()
        key = "test:ttl"
        assert key in store
        assert store[key]["ttl_remaining"] > 0

    def test_get_cache_store_returns_hits(self):
        @aspect_cache(ttl=60, key_fn=lambda: "test:hits")
        def f():
            return "x"

        f()
        f()
        f()
        store = get_cache_store()
        assert store["test:hits"]["hits"] == 2
