"""Tests unitaires - Pattern Proxy (CacheProxy)"""

import pytest
import time

from domain.integrations.smart_home_adapter import PhilipsHueAdapter
from domain.integrations.cache_proxy import CacheProxy


@pytest.fixture
def adapter():
    return PhilipsHueAdapter()


@pytest.fixture
def proxy(adapter):
    return CacheProxy(adapter, ttl=60)


@pytest.fixture
def short_ttl_proxy(adapter):
    return CacheProxy(adapter, ttl=1)


class TestCacheProxyBase:

    def test_proxy_implemente_adapter(self, proxy):
        """CacheProxy implemente SmartHomeAdapter"""
        from domain.integrations.smart_home_adapter import SmartHomeAdapter
        assert isinstance(proxy, SmartHomeAdapter)

    def test_proxy_delegue_nom(self, proxy):
        """Le nom de l'adapter est delegue"""
        assert proxy.get_adapter_name() == "philips-hue"

    def test_proxy_get_status(self, proxy):
        status = proxy.get_status()
        assert status["adapter"] == "philips-hue"
        assert status["connected"] is True

    def test_proxy_get_devices(self, proxy):
        devices = proxy.get_devices()
        assert isinstance(devices, list)
        assert len(devices) == 3


class TestCacheProxyHits:

    def test_premier_appel_miss(self, proxy):
        """Le premier appel est un cache miss"""
        proxy.get_status()
        stats = proxy.get_cache_stats()
        assert stats["misses"] == 1
        assert stats["hits"] == 0

    def test_deuxieme_appel_hit(self, proxy):
        """Le deuxieme appel est un cache hit"""
        proxy.get_status()
        proxy.get_status()
        stats = proxy.get_cache_stats()
        assert stats["hits"] == 1
        assert stats["misses"] == 1

    def test_devices_cache_separement(self, proxy):
        """get_status et get_devices ont des caches separes"""
        proxy.get_status()
        proxy.get_devices()
        proxy.get_status()
        proxy.get_devices()
        stats = proxy.get_cache_stats()
        assert stats["hits"] == 2
        assert stats["misses"] == 2

    def test_hit_ratio_calcul(self, proxy):
        """Le ratio de cache est calcule correctement"""
        proxy.get_status()
        proxy.get_status()
        proxy.get_status()
        stats = proxy.get_cache_stats()
        assert stats["hit_ratio"] == pytest.approx(2 / 3, rel=1e-2)


class TestCacheProxyInvalidation:

    def test_control_invalide_cache(self, proxy):
        """Une commande de controle invalide le cache"""
        proxy.get_status()
        proxy.get_devices()
        proxy.control_device("hue_001", {"action": "turn_off"})
        stats = proxy.get_cache_stats()
        assert "status" not in stats["cached_keys"]
        assert "devices" not in stats["cached_keys"]

    def test_invalidate_cle_specifique(self, proxy):
        """On peut invalider une cle specifique"""
        proxy.get_status()
        proxy.get_devices()
        proxy.invalidate("status")
        stats = proxy.get_cache_stats()
        assert "status" not in stats["cached_keys"]
        assert "devices" in stats["cached_keys"]

    def test_invalidate_tout(self, proxy):
        """On peut invalider tout le cache"""
        proxy.get_status()
        proxy.get_devices()
        proxy.invalidate()
        stats = proxy.get_cache_stats()
        assert stats["cached_keys"] == []

    def test_ttl_expire(self, short_ttl_proxy):
        """Apres le TTL, le cache est invalide"""
        short_ttl_proxy.get_status()
        time.sleep(1.1)
        short_ttl_proxy.get_status()
        stats = short_ttl_proxy.get_cache_stats()
        assert stats["misses"] == 2

    def test_control_toujours_direct(self, proxy):
        """Le controle bypass toujours le cache"""
        result = proxy.control_device("hue_001", {"action": "turn_on"})
        assert result["success"] is True

    def test_cache_stats_initial(self, proxy):
        """Les stats initiales sont a zero"""
        stats = proxy.get_cache_stats()
        assert stats["hits"] == 0
        assert stats["misses"] == 0
        assert stats["cached_keys"] == []
