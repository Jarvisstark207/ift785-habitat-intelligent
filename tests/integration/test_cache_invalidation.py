"""
Tests d'intégration - Cache invalidation (Itération 9 : AOP)
Teste les scénarios complets d'invalidation du cache @aspect_cache.
"""

import time
import pytest

from app.core.aspects import aspect_cache, invalidate_cache, get_cache_store, _cache_store


@pytest.fixture(autouse=True)
def clear_cache():
    invalidate_cache()
    yield
    invalidate_cache()


# ---------------------------------------------------------------------------
# Invalidation manuelle
# ---------------------------------------------------------------------------

class TestCacheInvalidationManual:
    def test_invalidate_all_clears_all_entries(self):
        @aspect_cache(ttl=60, key_fn=lambda: "k1")
        def f1():
            return 1

        @aspect_cache(ttl=60, key_fn=lambda: "k2")
        def f2():
            return 2

        f1()
        f2()
        count = invalidate_cache()
        assert count == 2
        assert len(_cache_store) == 0

    def test_invalidate_prefix_only_removes_matching(self):
        @aspect_cache(ttl=60, key_fn=lambda: "sensors:latest")
        def sensors():
            return [1, 2]

        @aspect_cache(ttl=60, key_fn=lambda: "devices:summary")
        def devices():
            return {"total": 5}

        sensors()
        devices()

        invalidate_cache(prefix="sensors:")
        store = get_cache_store()
        assert "sensors:latest" not in store
        assert "devices:summary" in store

    def test_invalidate_empty_prefix_clears_all(self):
        @aspect_cache(ttl=60, key_fn=lambda: "any:key")
        def func():
            return 42

        func()
        count = invalidate_cache("")
        assert count >= 1
        assert len(_cache_store) == 0

    def test_invalidate_returns_zero_when_empty(self):
        count = invalidate_cache()
        assert count == 0

    def test_double_invalidate_second_returns_zero(self):
        @aspect_cache(ttl=60, key_fn=lambda: "once")
        def func():
            return 1

        func()
        invalidate_cache()
        count = invalidate_cache()
        assert count == 0


# ---------------------------------------------------------------------------
# TTL naturel
# ---------------------------------------------------------------------------

class TestCacheInvalidationTTL:
    def test_entry_expires_after_ttl(self):
        call_count = [0]

        @aspect_cache(ttl=0.05)
        def compute():
            call_count[0] += 1
            return call_count[0]

        compute()
        time.sleep(0.1)
        compute()
        assert call_count[0] == 2

    def test_entry_valid_before_ttl(self):
        call_count = [0]

        @aspect_cache(ttl=10)
        def compute():
            call_count[0] += 1
            return call_count[0]

        compute()
        compute()
        assert call_count[0] == 1

    def test_ttl_remaining_decreases_over_time(self):
        @aspect_cache(ttl=60, key_fn=lambda: "ttl:check")
        def func():
            return "x"

        func()
        time.sleep(0.05)
        store = get_cache_store()
        assert store["ttl:check"]["ttl_remaining"] < 60.0


# ---------------------------------------------------------------------------
# Statistiques de cache
# ---------------------------------------------------------------------------

class TestCacheStats:
    def test_hits_increment_on_cache_hit(self):
        @aspect_cache(ttl=60, key_fn=lambda: "stats:hits")
        def func():
            return 1

        func()
        func()
        func()
        store = get_cache_store()
        assert store["stats:hits"]["hits"] == 2

    def test_misses_increment_on_cache_miss(self):
        call_count = [0]

        @aspect_cache(ttl=0.05, key_fn=lambda: "stats:misses")
        def func():
            call_count[0] += 1
            return call_count[0]

        func()
        time.sleep(0.1)
        func()
        store = get_cache_store()
        assert store["stats:misses"]["misses"] >= 2

    def test_first_call_is_miss(self):
        @aspect_cache(ttl=60, key_fn=lambda: "first:call")
        def func():
            return 1

        func()
        store = get_cache_store()
        assert store["first:call"]["misses"] >= 1

    def test_get_cache_store_returns_correct_structure(self):
        @aspect_cache(ttl=30, key_fn=lambda: "struct:test")
        def func():
            return "x"

        func()
        store = get_cache_store()
        entry = store["struct:test"]
        assert "ttl_remaining" in entry
        assert "hits" in entry
        assert "misses" in entry
        assert "value" in entry
