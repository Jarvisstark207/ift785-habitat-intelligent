"""
Aspects transversaux - Itération 9 : AOP en Python
@aspect_log   : journalisation avec niveau configurable
@aspect_cache : mise en cache TTL par fonction
@aspect_retry : retry avec backoff exponentiel
@aspect_audit : audit persistant en base de données

Chaque aspect est un décorateur pur, composable, sans couplage avec le code métier.
"""

import asyncio
import functools
import inspect
import logging
import time
import threading

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Cache interne partagé (utilisé par @aspect_cache)
# ---------------------------------------------------------------------------

_cache_store: dict = {}          # {cache_key: {"value": ..., "expires_at": float}}
_cache_lock = threading.Lock()
_cache_hits: dict = {}           # {cache_key: int} — nombre de hits
_cache_misses: dict = {}         # {cache_key: int} — nombre de misses


def get_cache_store() -> dict:
    """Retourne une copie du cache (pour les tests et l'UI)."""
    with _cache_lock:
        now = time.time()
        return {
            k: {
                "value": v["value"],
                "ttl_remaining": max(0.0, round(v["expires_at"] - now, 2)),
                "hits": _cache_hits.get(k, 0),
                "misses": _cache_misses.get(k, 0),
            }
            for k, v in _cache_store.items()
        }


def invalidate_cache(prefix: str = "") -> int:
    """Invalide les entrées dont la clé commence par *prefix*.  Retourne le nb invalidé."""
    with _cache_lock:
        if not prefix:
            count = len(_cache_store)
            _cache_store.clear()
            _cache_hits.clear()
            _cache_misses.clear()
            return count
        keys = [k for k in _cache_store if k.startswith(prefix)]
        for k in keys:
            del _cache_store[k]
            _cache_hits.pop(k, None)
            _cache_misses.pop(k, None)
        return len(keys)


def _make_cache_key(func, args, kwargs, key_fn=None):
    if key_fn is not None:
        return key_fn(*args, **kwargs)
    return f"{func.__module__}.{func.__qualname__}:{args}:{sorted(kwargs.items())}"


def _cache_get(key):
    with _cache_lock:
        entry = _cache_store.get(key)
        if entry and time.time() < entry["expires_at"]:
            _cache_hits[key] = _cache_hits.get(key, 0) + 1
            return True, entry["value"]
        _cache_misses[key] = _cache_misses.get(key, 0) + 1
        return False, None


def _cache_set(key, value, ttl):
    with _cache_lock:
        _cache_store[key] = {"value": value, "expires_at": time.time() + ttl}
