"""Tests d'integration - APIs tierces (Adapter + Proxy + Decorator)"""

import pytest

from domain.integrations.smart_home_adapter import (
    PhilipsHueAdapter,
    NestAdapter,
    GenericAdapter,
)
from domain.integrations.cache_proxy import CacheProxy
from domain.integrations.decorators import LoggingDecorator, ValidationDecorator


class TestAdapterIntegration:

    def test_hue_adapter_status_complet(self):
        """Le statut Hue contient tous les champs requis"""
        adapter = PhilipsHueAdapter()
        status = adapter.get_status()
        assert status["connected"] is True
        assert status["total_devices"] > 0
        assert status["active_devices"] >= 0

    def test_hue_controle_puis_statut(self):
        """Controle d'un appareil et verification du statut"""
        adapter = PhilipsHueAdapter()
        adapter.control_device("hue_002", {"action": "turn_on"})
        devices = adapter.get_devices()
        hue_002 = next(d for d in devices if d["id"] == "hue_002")
        assert hue_002["status"] == "on"

    def test_nest_thermostat_temperature(self):
        """Changement de temperature via Nest adapter"""
        adapter = NestAdapter()
        adapter.control_device("nest_therm_01", {
            "action": "set_temperature", "value": 23.0
        })
        devices = adapter.get_devices()
        therm = next(d for d in devices if d["id"] == "nest_therm_01")
        assert therm["properties"]["target_temp"] == 23.0

    def test_generic_cycle_on_off(self):
        """Cycle on/off sur le generic adapter"""
        adapter = GenericAdapter()
        adapter.control_device("generic_001", {"action": "turn_off"})
        devices_off = adapter.get_devices()
        dev = next(d for d in devices_off if d["id"] == "generic_001")
        assert dev["status"] == "off"

        adapter.control_device("generic_001", {"action": "turn_on"})
        devices_on = adapter.get_devices()
        dev = next(d for d in devices_on if d["id"] == "generic_001")
        assert dev["status"] == "on"

    def test_tous_adapters_meme_interface(self):
        """Tous les adapters retournent le meme format de base"""
        adapters = [PhilipsHueAdapter(), NestAdapter(), GenericAdapter()]
        for adapter in adapters:
            status = adapter.get_status()
            assert "adapter" in status
            assert "connected" in status
            assert "total_devices" in status

            devices = adapter.get_devices()
            for device in devices:
                assert "id" in device
                assert "name" in device
                assert "type" in device
                assert "status" in device


class TestProxyAvecAdapter:

    def test_proxy_hue_status_identique(self):
        """Le proxy retourne le meme resultat que l'adapter"""
        adapter = PhilipsHueAdapter()
        proxy = CacheProxy(adapter, ttl=60)
        assert proxy.get_status() == adapter.get_status()

    def test_proxy_cache_puis_invalidation(self):
        """Workflow complet: mise en cache puis invalidation"""
        proxy = CacheProxy(PhilipsHueAdapter(), ttl=60)
        proxy.get_status()
        proxy.get_devices()

        stats_avant = proxy.get_cache_stats()
        assert len(stats_avant["cached_keys"]) == 2

        proxy.control_device("hue_001", {"action": "turn_off"})
        stats_apres = proxy.get_cache_stats()
        assert len(stats_apres["cached_keys"]) == 0

    def test_proxy_avec_nest(self):
        """Le proxy fonctionne avec NestAdapter"""
        proxy = CacheProxy(NestAdapter(), ttl=60)
        proxy.get_devices()
        proxy.get_devices()
        assert proxy.get_cache_stats()["hits"] == 1


class TestDecoratorAvecProxy:

    def test_logging_autour_de_proxy(self):
        """Composition: LoggingDecorator wraps CacheProxy wraps Adapter"""
        adapter = PhilipsHueAdapter()
        proxy = CacheProxy(adapter, ttl=60)
        logged = LoggingDecorator(proxy)

        logged.get_status()
        logged.get_devices()
        logged.control_device("hue_001", {"action": "turn_on"})

        assert logged.get_log_count() == 3
        assert logged.get_adapter_name() == "philips-hue"

    def test_validation_detecte_erreur(self):
        """ValidationDecorator detecte les erreurs de structure"""
        from domain.integrations.smart_home_adapter import SmartHomeAdapter

        class BrokenAdapter(SmartHomeAdapter):
            def get_status(self):
                return {"wrong_key": True}  # Manque 'adapter', 'connected'

            def get_devices(self):
                return []

            def control_device(self, device_id, command):
                return {}

            def get_adapter_name(self):
                return "broken"

        broken = ValidationDecorator(BrokenAdapter())
        with pytest.raises(ValueError):
            broken.get_status()
