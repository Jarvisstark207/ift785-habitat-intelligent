"""Tests pour la classe Room"""
import pytest
from domain.models.sensor import Sensor
from domain.models.device import Device
from domain.models.room import Room


# ─── Fixtures ────────────────────────────────────────────────────────────────

@pytest.fixture
def room_vide():
    return Room(name="salon")


@pytest.fixture
def device_a():
    d = Device(device_id="d1", room_name="salon")
    d.add_sensor(Sensor(sensor_id="s1", type="temperature", unit="C"))
    return d


@pytest.fixture
def device_b():
    return Device(device_id="d2", room_name="salon")


# ─── Tests Room ───────────────────────────────────────────────────────────────

class TestRoom:

    def test_creation(self, room_vide):
        assert room_vide.name == "salon"
        assert room_vide.devices == []

    def test_add_device(self, room_vide, device_a):
        room_vide.add_device(device_a)
        assert len(room_vide.devices) == 1
        assert room_vide.devices[0] is device_a

    def test_add_plusieurs_devices(self, room_vide, device_a, device_b):
        room_vide.add_device(device_a)
        room_vide.add_device(device_b)
        assert len(room_vide.devices) == 2

    def test_get_device_count_vide(self, room_vide):
        assert room_vide.get_device_count() == 0

    def test_get_device_count_un(self, room_vide, device_a):
        room_vide.add_device(device_a)
        assert room_vide.get_device_count() == 1

    def test_get_device_count_plusieurs(self, room_vide, device_a, device_b):
        room_vide.add_device(device_a)
        room_vide.add_device(device_b)
        assert room_vide.get_device_count() == 2

    def test_noms_differents(self):
        cuisine = Room(name="cuisine")
        chambre = Room(name="chambre")
        assert cuisine.name != chambre.name

    def test_devices_independants_par_room(self, device_a):
        salon = Room(name="salon")
        cuisine = Room(name="cuisine")
        salon.add_device(device_a)
        assert salon.get_device_count() == 1
        assert cuisine.get_device_count() == 0