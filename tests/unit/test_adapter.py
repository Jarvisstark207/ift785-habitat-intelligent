"""Tests unitaires - Pattern Adapter (SmartHome integrations)"""

import pytest

from domain.integrations.smart_home_adapter import (
    SmartHomeAdapter,
    PhilipsHueAdapter,
    NestAdapter,
    GenericAdapter,
)


class TestSmartHomeAdapterInterface:

    def test_adapter_est_abstrait(self):
        """SmartHomeAdapter ne peut pas etre instancie directement"""
        with pytest.raises(TypeError):
            SmartHomeAdapter()

    def test_philips_hue_est_adapter(self):
        """PhilipsHueAdapter implemente SmartHomeAdapter"""
        adapter = PhilipsHueAdapter()
        assert isinstance(adapter, SmartHomeAdapter)

    def test_nest_est_adapter(self):
        """NestAdapter implemente SmartHomeAdapter"""
        assert isinstance(NestAdapter(), SmartHomeAdapter)

    def test_generic_est_adapter(self):
        """GenericAdapter implemente SmartHomeAdapter"""
        assert isinstance(GenericAdapter(), SmartHomeAdapter)


class TestPhilipsHueAdapter:

    @pytest.fixture
    def hue(self):
        return PhilipsHueAdapter()

    def test_get_adapter_name(self, hue):
        assert hue.get_adapter_name() == "philips-hue"

    def test_get_status_retourne_dict(self, hue):
        status = hue.get_status()
        assert isinstance(status, dict)
        assert status["adapter"] == "philips-hue"
        assert status["connected"] is True

    def test_get_status_contient_total(self, hue):
        status = hue.get_status()
        assert "total_devices" in status
        assert status["total_devices"] == 3

    def test_get_devices_retourne_liste(self, hue):
        devices = hue.get_devices()
        assert isinstance(devices, list)
        assert len(devices) == 3

    def test_get_devices_structure(self, hue):
        device = hue.get_devices()[0]
        assert "id" in device
        assert "name" in device
        assert "type" in device
        assert "status" in device
        assert device["source"] == "philips-hue"

    def test_control_device_turn_on(self, hue):
        result = hue.control_device("hue_002", {"action": "turn_on"})
        assert result["success"] is True

    def test_control_device_turn_off(self, hue):
        result = hue.control_device("hue_001", {"action": "turn_off"})
        assert result["success"] is True

    def test_control_device_inexistant(self, hue):
        result = hue.control_device("hue_999", {"action": "turn_on"})
        assert result["success"] is False


class TestNestAdapter:

    @pytest.fixture
    def nest(self):
        return NestAdapter()

    def test_get_adapter_name(self, nest):
        assert nest.get_adapter_name() == "nest"

    def test_get_status_retourne_dict(self, nest):
        status = nest.get_status()
        assert status["adapter"] == "nest"
        assert status["connected"] is True

    def test_get_devices_retourne_thermostat_et_camera(self, nest):
        devices = nest.get_devices()
        types = {d["type"] for d in devices}
        assert "thermostat" in types
        assert "camera" in types

    def test_control_temperature(self, nest):
        result = nest.control_device("nest_therm_01", {
            "action": "set_temperature", "value": 22.0
        })
        assert result["success"] is True

    def test_control_inexistant(self, nest):
        result = nest.control_device("nest_999", {"action": "set_temperature"})
        assert result["success"] is False


class TestGenericAdapter:

    @pytest.fixture
    def generic(self):
        return GenericAdapter()

    def test_get_adapter_name(self, generic):
        assert generic.get_adapter_name() == "generic"

    def test_get_status(self, generic):
        status = generic.get_status()
        assert status["adapter"] == "generic"
        assert "total_devices" in status

    def test_get_devices(self, generic):
        devices = generic.get_devices()
        assert len(devices) >= 1

    def test_control_turn_off(self, generic):
        result = generic.control_device("generic_001", {"action": "turn_off"})
        assert result["success"] is True
