"""Tests d'integration - CacheProxy avec differents adapters"""

import pytest
import time

from domain.integrations.smart_home_adapter import (
    PhilipsHueAdapter,
    NestAdapter,
    GenericAdapter,
)
from domain.integrations.cache_proxy import CacheProxy


class TestCacheProxyIntegration:

    def test_cache_partage_entre_appels(self):
        """Le cache est reutilise entre plusieurs appels identiques"""
        proxy = CacheProxy(PhilipsHueAdapter(), ttl=60)
        result1 = proxy.get_status()
        result2 = proxy.get_status()
        result3 = proxy.get_status()
        assert result1 == result2 == result3
        stats = proxy.get_cache_stats()
        assert stats["hits"] == 2
        assert stats["misses"] == 1

    def test_cache_independant_par_methode(self):
        """get_status et get_devices ont des caches independants"""
        proxy = CacheProxy(NestAdapter(), ttl=60)
        proxy.get_status()
        proxy.get_devices()
        proxy.get_status()
        proxy.get_devices()
        stats = proxy.get_cache_stats()
        assert stats["misses"] == 2
        assert stats["hits"] == 2

    def test_control_refreshe_le_cache(self):
        """Apres une commande, les donnees sont refraichies"""
        proxy = CacheProxy(PhilipsHueAdapter(), ttl=60)
        proxy.get_devices()
        proxy.control_device("hue_002", {"action": "turn_on"})
        proxy.get_devices()
        assert proxy.get_cache_stats()["misses"] == 2

    def test_proxy_generic_adapter(self):
        """Le proxy fonctionne avec GenericAdapter"""
        proxy = CacheProxy(GenericAdapter(), ttl=60)
        s1 = proxy.get_status()
        s2 = proxy.get_status()
        assert s1 == s2
        assert proxy.get_cache_stats()["hits"] == 1

    def test_ttl_court_expire(self):
        """Le cache expire selon le TTL"""
        proxy = CacheProxy(PhilipsHueAdapter(), ttl=1)
        proxy.get_status()
        time.sleep(1.1)
        proxy.get_status()
        stats = proxy.get_cache_stats()
        assert stats["misses"] == 2

    def test_invalidation_manuelle_force_refresh(self):
        """L'invalidation manuelle force un nouveau fetch"""
        proxy = CacheProxy(PhilipsHueAdapter(), ttl=60)
        proxy.get_status()
        proxy.invalidate("status")
        proxy.get_status()
        stats = proxy.get_cache_stats()
        assert stats["misses"] == 2
        assert stats["hits"] == 0

    def test_hit_ratio_apres_workflow(self):
        """Ratio de cache apres un workflow complet"""
        proxy = CacheProxy(NestAdapter(), ttl=60)
        proxy.get_status()   # miss
        proxy.get_status()   # hit
        proxy.get_status()   # hit
        proxy.get_devices()  # miss
        proxy.get_devices()  # hit
        stats = proxy.get_cache_stats()
        assert stats["hits"] == 3
        assert stats["misses"] == 2
        assert stats["hit_ratio"] == pytest.approx(0.6, rel=1e-2)
