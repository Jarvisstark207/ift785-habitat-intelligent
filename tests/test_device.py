"""Tests pour la classe Device et Sensor"""
import pytest
from domain.models.sensor import Sensor
from domain.models.device import Device


# ─── Fixtures ────────────────────────────────────────────────────────────────

@pytest.fixture
def sensor_temp():
    return Sensor(sensor_id="s1", type="temperature", unit="C", location="salon")


@pytest.fixture
def sensor_lumiere():
    return Sensor(sensor_id="s2", type="lumiere", unit="lux", location="salon")


@pytest.fixture
def device_vide():
    return Device(device_id="d1", room_name="salon")


@pytest.fixture
def device_avec_capteurs(sensor_temp, sensor_lumiere):
    d = Device(device_id="d1", room_name="salon")
    d.add_sensor(sensor_temp)
    d.add_sensor(sensor_lumiere)
    return d


# ─── Tests Sensor ─────────────────────────────────────────────────────────────

class TestSensor:

    def test_creation(self):
        s = Sensor(sensor_id="s1", type="temperature", unit="C")
        assert s.sensor_id == "s1"
        assert s.type == "temperature"
        assert s.unit == "C"
        assert s.location is None

    def test_creation_avec_location(self):
        s = Sensor(sensor_id="s2", type="lumiere", unit="lux", location="cuisine")
        assert s.location == "cuisine"

    def test_matches_type_vrai(self, sensor_temp):
        assert sensor_temp.matches_type("temperature") is True

    def test_matches_type_faux(self, sensor_temp):
        assert sensor_temp.matches_type("lumiere") is False

    def test_matches_type_case_sensitive(self, sensor_temp):
        assert sensor_temp.matches_type("Temperature") is False


# ─── Tests Device ─────────────────────────────────────────────────────────────

class TestDevice:

    def test_creation(self, device_vide):
        assert device_vide.device_id == "d1"
        assert device_vide.room_name == "salon"
        assert device_vide.sensors == []

    def test_add_sensor(self, device_vide, sensor_temp):
        device_vide.add_sensor(sensor_temp)
        assert len(device_vide.sensors) == 1
        assert device_vide.sensors[0] is sensor_temp

    def test_add_plusieurs_capteurs(self, device_vide, sensor_temp, sensor_lumiere):
        device_vide.add_sensor(sensor_temp)
        device_vide.add_sensor(sensor_lumiere)
        assert len(device_vide.sensors) == 2

    def test_get_sensor_by_type_trouve(self, device_avec_capteurs):
        s = device_avec_capteurs.get_sensor_by_type("temperature")
        assert s is not None
        assert s.type == "temperature"

    def test_get_sensor_by_type_non_trouve(self, device_avec_capteurs):
        s = device_avec_capteurs.get_sensor_by_type("mouvement")
        assert s is None

    def test_get_sensor_by_type_device_vide(self, device_vide):
        s = device_vide.get_sensor_by_type("temperature")
        assert s is None

    def test_get_all_sensor_types(self, device_avec_capteurs):
        types = device_avec_capteurs.get_all_sensor_types()
        assert "temperature" in types
        assert "lumiere" in types
        assert len(types) == 2

    def test_get_all_sensor_types_vide(self, device_vide):
        types = device_vide.get_all_sensor_types()
        assert types == []