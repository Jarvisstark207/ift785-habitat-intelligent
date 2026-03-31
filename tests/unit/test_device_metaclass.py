"""
Tests unitaires - Registre de devices par métaclasse (Itération 8)
Couvre : DeviceMeta, DeviceBase, enregistrement automatique des sous-classes.
"""

import pytest
from domain.models.device_meta import (
    DeviceMeta,
    DeviceBase,
    TemperatureSensor,
    MotionDetector,
    instantiate_from_registry,
)


# ---------------------------------------------------------------------------
# DeviceMeta - registre automatique
# ---------------------------------------------------------------------------

class TestDeviceMetaRegistry:
    def test_temperature_sensor_auto_registered(self):
        assert "TemperatureSensor" in DeviceMeta.registry

    def test_motion_detector_auto_registered(self):
        assert "MotionDetector" in DeviceMeta.registry

    def test_humidity_sensor_auto_registered(self):
        assert "HumiditySensor" in DeviceMeta.registry

    def test_device_base_not_registered(self):
        # DeviceBase lui-même ne doit pas s'enregistrer (pas de bases)
        assert "DeviceBase" not in DeviceMeta.registry

    def test_new_subclass_auto_registers(self):
        class NewSensor(DeviceBase):
            pass
        assert "NewSensor" in DeviceMeta.registry

    def test_registry_contains_correct_class(self):
        assert DeviceMeta.registry["TemperatureSensor"] is TemperatureSensor
        assert DeviceMeta.registry["MotionDetector"] is MotionDetector

    def test_device_registry_alias(self):
        assert "TemperatureSensor" in DeviceMeta.device_registry

    def test_get_registry_returns_copy(self):
        reg = DeviceMeta.get_registry()
        assert isinstance(reg, dict)
        assert "TemperatureSensor" in reg

    def test_get_device_class_known_type(self):
        cls = DeviceMeta.get_device_class("TemperatureSensor")
        assert cls is TemperatureSensor

    def test_get_device_class_unknown_type(self):
        cls = DeviceMeta.get_device_class("NonExistentDevice")
        assert cls is None

    def test_multiple_subclasses_all_registered(self):
        class SensorA(DeviceBase):
            pass

        class SensorB(DeviceBase):
            pass

        assert "SensorA" in DeviceMeta.registry
        assert "SensorB" in DeviceMeta.registry


# ---------------------------------------------------------------------------
# DeviceBase - descripteurs
# ---------------------------------------------------------------------------

class TestDeviceBase:
    def test_create_with_valid_name(self):
        d = DeviceBase.__new__(DeviceBase)
        object.__setattr__(d, '_name_val', None)
        d.name = "My Device"
        assert d.name == "My Device"

    def test_temperature_sensor_valid_name(self):
        s = TemperatureSensor(name="Kitchen Sensor")
        assert s.name == "Kitchen Sensor"

    def test_temperature_sensor_valid_status(self):
        s = TemperatureSensor(status="inactive")
        assert s.status == "inactive"

    def test_invalid_status_raises_valueerror(self):
        s = TemperatureSensor()
        with pytest.raises(ValueError):
            s.status = "broken"

    def test_name_wrong_type_raises_typeerror(self):
        s = TemperatureSensor()
        with pytest.raises(TypeError):
            s.name = 12345

    def test_name_max_length(self):
        s = TemperatureSensor()
        with pytest.raises(ValueError):
            s.name = "a" * 129  # > 128 chars


# ---------------------------------------------------------------------------
# TemperatureSensor
# ---------------------------------------------------------------------------

class TestTemperatureSensor:
    def test_default_temperature(self):
        s = TemperatureSensor()
        assert s.temperature == 20.0

    def test_valid_temperature(self):
        s = TemperatureSensor(temperature=36.6)
        assert s.temperature == 36.6

    def test_temperature_out_of_range_high(self):
        s = TemperatureSensor()
        with pytest.raises(ValueError):
            s.temperature = 999

    def test_temperature_out_of_range_low(self):
        s = TemperatureSensor()
        with pytest.raises(ValueError):
            s.temperature = -100

    def test_boundary_min(self):
        s = TemperatureSensor()
        s.temperature = -50
        assert s.temperature == -50

    def test_boundary_max(self):
        s = TemperatureSensor()
        s.temperature = 100
        assert s.temperature == 100

    def test_to_dict(self):
        s = TemperatureSensor(name="T1", temperature=25.0)
        d = s.to_dict()
        assert d["type"] == "TemperatureSensor"
        assert d["name"] == "T1"
        assert d["temperature"] == 25.0


# ---------------------------------------------------------------------------
# MotionDetector
# ---------------------------------------------------------------------------

class TestMotionDetector:
    def test_default_sensitivity(self):
        m = MotionDetector()
        assert m.sensitivity == 5

    def test_sensitivity_out_of_range(self):
        m = MotionDetector()
        with pytest.raises(ValueError):
            m.sensitivity = 11

    def test_sensitivity_min_boundary(self):
        m = MotionDetector()
        m.sensitivity = 1
        assert m.sensitivity == 1

    def test_to_dict(self):
        m = MotionDetector(name="M1", sensitivity=7)
        d = m.to_dict()
        assert d["type"] == "MotionDetector"
        assert d["sensitivity"] == 7


# ---------------------------------------------------------------------------
# instantiate_from_registry
# ---------------------------------------------------------------------------

class TestInstantiateFromRegistry:
    def test_instantiate_temperature_sensor(self):
        device = instantiate_from_registry("TemperatureSensor", temperature=22.0)
        assert isinstance(device, TemperatureSensor)
        assert device.temperature == 22.0

    def test_instantiate_motion_detector(self):
        device = instantiate_from_registry("MotionDetector", sensitivity=3)
        assert isinstance(device, MotionDetector)
        assert device.sensitivity == 3

    def test_unknown_type_raises_valueerror(self):
        with pytest.raises(ValueError, match="Type de device inconnu"):
            instantiate_from_registry("UnknownDevice")
