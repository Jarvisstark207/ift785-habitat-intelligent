"""
Tests unitaires - Descripteurs de validation (Itération 8)
Couvre : TypedField, RangedField (__get__, __set__)
"""

import pytest
from app.core.descriptors import TypedField, RangedField


# ---------------------------------------------------------------------------
# Classes de test utilisant les descripteurs
# ---------------------------------------------------------------------------

class PersonModel:
    name = TypedField(str, max_length=10)
    age = RangedField(min_val=0, max_val=150)
    status = TypedField(str, allowed=["active", "inactive"])


class DeviceModel:
    name = TypedField(str, max_length=128)
    status = TypedField(str, allowed=["active", "inactive", "error"])
    temperature = RangedField(min_val=-50, max_val=100)
    sensitivity = RangedField(min_val=1, max_val=10)


class SensorReadingModel:
    sensor_type = TypedField(str, allowed=["temperature", "humidity", "motion"])
    value = RangedField(min_val=-1000, max_val=1000)
    unit = TypedField(str, max_length=20)


# ---------------------------------------------------------------------------
# TypedField
# ---------------------------------------------------------------------------

class TestTypedField:
    def test_set_and_get_valid_value(self):
        obj = PersonModel()
        obj.name = "Alice"
        assert obj.name == "Alice"

    def test_wrong_type_raises_typeerror(self):
        obj = PersonModel()
        with pytest.raises(TypeError):
            obj.name = 12345

    def test_wrong_type_not_assertionerror(self):
        obj = PersonModel()
        try:
            obj.name = 12345
        except AssertionError:
            pytest.fail("TypedField ne doit pas lever AssertionError")
        except TypeError:
            pass

    def test_max_length_valid(self):
        obj = PersonModel()
        obj.name = "Bob"  # len 3, max 10
        assert obj.name == "Bob"

    def test_max_length_exceeded_raises_valueerror(self):
        obj = PersonModel()
        with pytest.raises(ValueError):
            obj.name = "TooLongName!"  # > 10 chars

    def test_not_valueerror_for_type(self):
        obj = PersonModel()
        try:
            obj.name = 42
        except TypeError:
            pass
        except ValueError:
            pytest.fail("Une erreur de type doit être TypeError, pas ValueError")

    def test_allowed_valid_value(self):
        obj = PersonModel()
        obj.status = "active"
        assert obj.status == "active"

    def test_allowed_invalid_value_raises_valueerror(self):
        obj = PersonModel()
        with pytest.raises(ValueError):
            obj.status = "unknown"

    def test_get_returns_none_before_set(self):
        obj = PersonModel()
        assert obj.name is None

    def test_class_access_returns_descriptor(self):
        descriptor = PersonModel.name
        assert isinstance(descriptor, TypedField)

    def test_multiple_instances_independent(self):
        obj1 = PersonModel()
        obj2 = PersonModel()
        obj1.name = "Alice"
        obj2.name = "Bob"
        assert obj1.name == "Alice"
        assert obj2.name == "Bob"

    def test_typed_field_on_device_model(self):
        d = DeviceModel()
        d.name = "My Device"
        assert d.name == "My Device"

    def test_typed_field_wrong_type_raises_typeerror_not_valueerror(self):
        d = DeviceModel()
        with pytest.raises(TypeError):
            d.name = 42

    def test_typed_field_allowed_on_device(self):
        d = DeviceModel()
        d.status = "error"
        assert d.status == "error"

    def test_typed_field_disallowed_on_device(self):
        d = DeviceModel()
        with pytest.raises(ValueError):
            d.status = "broken"

    def test_sensor_reading_type_field(self):
        r = SensorReadingModel()
        r.sensor_type = "temperature"
        assert r.sensor_type == "temperature"

    def test_sensor_reading_unit_max_length(self):
        r = SensorReadingModel()
        with pytest.raises(ValueError):
            r.unit = "a" * 21  # > 20 chars


# ---------------------------------------------------------------------------
# RangedField
# ---------------------------------------------------------------------------

class TestRangedField:
    def test_set_and_get_valid_value(self):
        obj = PersonModel()
        obj.age = 30
        assert obj.age == 30

    def test_value_below_min_raises_valueerror(self):
        obj = PersonModel()
        with pytest.raises(ValueError):
            obj.age = -1

    def test_value_above_max_raises_valueerror(self):
        obj = PersonModel()
        with pytest.raises(ValueError):
            obj.age = 200

    def test_boundary_min_valid(self):
        obj = PersonModel()
        obj.age = 0
        assert obj.age == 0

    def test_boundary_max_valid(self):
        obj = PersonModel()
        obj.age = 150
        assert obj.age == 150

    def test_not_assertionerror(self):
        obj = PersonModel()
        try:
            obj.age = -1
        except AssertionError:
            pytest.fail("RangedField ne doit pas lever AssertionError")
        except ValueError:
            pass

    def test_non_numeric_raises_typeerror(self):
        obj = PersonModel()
        with pytest.raises(TypeError):
            obj.age = "thirty"

    def test_float_value_valid(self):
        d = DeviceModel()
        d.temperature = 36.6
        assert d.temperature == 36.6

    def test_temperature_too_high(self):
        d = DeviceModel()
        with pytest.raises(ValueError):
            d.temperature = 999

    def test_temperature_too_low(self):
        d = DeviceModel()
        with pytest.raises(ValueError):
            d.temperature = -100

    def test_sensitivity_valid(self):
        d = DeviceModel()
        d.sensitivity = 5
        assert d.sensitivity == 5

    def test_sensitivity_out_of_range(self):
        d = DeviceModel()
        with pytest.raises(ValueError):
            d.sensitivity = 11

    def test_class_access_returns_descriptor(self):
        descriptor = PersonModel.age
        assert isinstance(descriptor, RangedField)

    def test_multiple_instances_independent(self):
        d1 = DeviceModel()
        d2 = DeviceModel()
        d1.temperature = 20.0
        d2.temperature = 35.0
        assert d1.temperature == 20.0
        assert d2.temperature == 35.0

    def test_get_returns_none_before_set(self):
        obj = PersonModel()
        assert obj.age is None

    def test_sensor_reading_value_valid(self):
        r = SensorReadingModel()
        r.value = 42.5
        assert r.value == 42.5

    def test_sensor_reading_value_out_of_range(self):
        r = SensorReadingModel()
        with pytest.raises(ValueError):
            r.value = 9999
