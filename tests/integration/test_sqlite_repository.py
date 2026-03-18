"""
Tests d'integration pour le Repository SQLAlchemy avec SQLite - Iteration 6
"""

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from infrastructure.db.sqlalchemy_models import Base, DeviceRecord
from infrastructure.db.device_repository import DeviceRepository


@pytest.fixture
def sqlite_engine():
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    yield engine
    Base.metadata.drop_all(engine)
    engine.dispose()


@pytest.fixture
def session(sqlite_engine):
    Session = sessionmaker(bind=sqlite_engine)
    s = Session()
    yield s
    s.close()


@pytest.fixture
def repo(session):
    return DeviceRepository(session)


class TestDeviceRepositoryIntegrationSave:
    def test_save_and_retrieve(self, repo, session):
        device = DeviceRecord(
            device_id="d-001",
            name="Lampe",
            room_name="salon",
            device_type="light",
            manufacturer="Philips",
        )
        repo.save(device)
        session.commit()
        found = repo.find_by_id("d-001")
        assert found is not None
        assert found.name == "Lampe"
        assert found.room_name == "salon"

    def test_save_multiple_devices(self, repo, session):
        for i in range(5):
            device = DeviceRecord(
                device_id=f"dev-{i}",
                name=f"Device {i}",
                device_type="sensor",
            )
            repo.save(device)
        session.commit()
        all_devices = repo.find_all()
        assert len(all_devices) == 5

    def test_update_existing_device(self, repo, session):
        device = DeviceRecord(
            device_id="d-002",
            name="Original Name",
            device_type="light",
        )
        repo.save(device)
        session.commit()

        updated = DeviceRecord(
            device_id="d-002",
            name="Updated Name",
            device_type="thermostat",
            manufacturer="Nest",
        )
        repo.save(updated)
        session.commit()

        found = repo.find_by_id("d-002")
        assert found.name == "Updated Name"
        assert found.device_type == "thermostat"


class TestDeviceRepositoryIntegrationQuery:
    def test_find_by_type(self, repo, session):
        repo.save(DeviceRecord(device_id="l1", name="Light 1", device_type="light"))
        repo.save(DeviceRecord(device_id="l2", name="Light 2", device_type="light"))
        repo.save(DeviceRecord(device_id="t1", name="Thermo", device_type="thermostat"))
        session.commit()

        lights = repo.find_by_type("light")
        thermos = repo.find_by_type("thermostat")
        assert len(lights) == 2
        assert len(thermos) == 1

    def test_find_by_room(self, repo, session):
        repo.save(DeviceRecord(device_id="s1", name="Salon 1", room_name="salon"))
        repo.save(DeviceRecord(device_id="s2", name="Salon 2", room_name="salon"))
        repo.save(DeviceRecord(device_id="c1", name="Cuisine 1", room_name="cuisine"))
        session.commit()

        salon_devices = repo.find_by_room("salon")
        assert len(salon_devices) == 2

    def test_find_by_id_not_found(self, repo):
        result = repo.find_by_id("nonexistent")
        assert result is None

    def test_count(self, repo, session):
        for i in range(3):
            repo.save(DeviceRecord(device_id=f"cnt-{i}", name=f"Device {i}"))
        session.commit()
        assert repo.count() == 3

    def test_count_empty(self, repo):
        assert repo.count() == 0


class TestDeviceRepositoryIntegrationDelete:
    def test_delete_existing(self, repo, session):
        repo.save(DeviceRecord(device_id="del-1", name="To Delete"))
        session.commit()
        result = repo.delete("del-1")
        session.commit()
        assert result is True
        assert repo.find_by_id("del-1") is None

    def test_delete_nonexistent(self, repo):
        result = repo.delete("ghost")
        assert result is False

    def test_delete_reduces_count(self, repo, session):
        repo.save(DeviceRecord(device_id="x1", name="X1"))
        repo.save(DeviceRecord(device_id="x2", name="X2"))
        session.commit()
        repo.delete("x1")
        session.commit()
        assert repo.count() == 1

    def test_to_dict(self, repo, session):
        repo.save(DeviceRecord(
            device_id="d3",
            name="Test",
            room_name="kitchen",
            device_type="sensor",
            manufacturer="Generic",
            status="active",
        ))
        session.commit()
        found = repo.find_by_id("d3")
        d = found.to_dict()
        assert d["device_id"] == "d3"
        assert d["room_name"] == "kitchen"
