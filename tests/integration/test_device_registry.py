"""
Tests d'intégration - Registre de devices par métaclasse (Itération 8)
Vérifie l'endpoint GET /api/devices/types et l'enregistrement automatique.
"""

import pytest
from fastapi.testclient import TestClient

from app import app
from domain.models.device_meta import DeviceMeta, DeviceBase, instantiate_from_registry

client = TestClient(app)


# ---------------------------------------------------------------------------
# GET /api/devices/types
# ---------------------------------------------------------------------------

class TestDeviceTypesEndpoint:
    def test_endpoint_returns_success(self):
        response = client.get("/api/devices/types")
        assert response.status_code == 200

    def test_response_structure(self):
        response = client.get("/api/devices/types")
        data = response.json()
        assert "count" in data
        assert "types" in data
        assert isinstance(data["types"], list)

    def test_metaclass_devices_are_listed(self):
        response = client.get("/api/devices/types")
        types = response.json()["types"]
        assert "TemperatureSensor" in types
        assert "MotionDetector" in types
        assert "HumiditySensor" in types

    def test_count_equals_types_length(self):
        response = client.get("/api/devices/types")
        data = response.json()
        assert data["count"] == len(data["types"])

    def test_new_type_appears_in_endpoint(self):
        class DynamicSensor(DeviceBase):
            pass

        response = client.get("/api/devices/types")
        types = response.json()["types"]
        assert "DynamicSensor" in types


# ---------------------------------------------------------------------------
# Métaclasse - enregistrement automatique
# ---------------------------------------------------------------------------

class TestDeviceMetaAutoRegister:
    def test_subclass_auto_registers(self):
        class ProximitySensor(DeviceBase):
            pass
        assert "ProximitySensor" in DeviceMeta.registry

    def test_deep_inheritance_registers(self):
        class BaseSensor(DeviceBase):
            pass

        class ExtendedSensor(BaseSensor):
            pass

        assert "ExtendedSensor" in DeviceMeta.registry

    def test_registry_maps_to_correct_class(self):
        from domain.models.device_meta import TemperatureSensor
        assert DeviceMeta.registry["TemperatureSensor"] is TemperatureSensor

    def test_registry_is_persistent(self):
        reg1 = DeviceMeta.get_registry()
        reg2 = DeviceMeta.get_registry()
        assert set(reg1.keys()) == set(reg2.keys())


# ---------------------------------------------------------------------------
# Désérialisation via registre
# ---------------------------------------------------------------------------

class TestInstantiateFromRegistry:
    def test_temperature_sensor_from_json(self):
        device = instantiate_from_registry(
            "TemperatureSensor", name="T1", temperature=25.0
        )
        from domain.models.device_meta import TemperatureSensor
        assert isinstance(device, TemperatureSensor)
        assert device.name == "T1"
        assert device.temperature == 25.0

    def test_motion_detector_from_json(self):
        device = instantiate_from_registry(
            "MotionDetector", name="M1", sensitivity=8
        )
        from domain.models.device_meta import MotionDetector
        assert isinstance(device, MotionDetector)
        assert device.sensitivity == 8

    def test_unknown_type_raises_valueerror(self):
        with pytest.raises(ValueError):
            instantiate_from_registry("GhostDevice")

    def test_to_dict_contains_type_name(self):
        device = instantiate_from_registry("TemperatureSensor", temperature=20.0)
        d = device.to_dict()
        assert d["type"] == "TemperatureSensor"
