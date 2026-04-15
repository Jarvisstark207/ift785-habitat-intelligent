"""
Tests d'integration - Repository avec interface PostgreSQL-compatible (Iter 10)

En mode test, utilise SQLite en memoire.
Verifie que l'interface Repository est independante du moteur.
"""

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from infrastructure.db.sqlalchemy_models import Base, DeviceRecord
from infrastructure.db.device_repository import DeviceRepository
from infrastructure.db.unit_of_work import SQLAlchemyUnitOfWork


def make_record(**kwargs):
    """Cree un DeviceRecord SQLAlchemy a partir de kwargs."""
    defaults = {
        "device_id": "x", "name": "X",
        "room_name": "", "device_type": "", "manufacturer": "",
    }
    defaults.update(kwargs)
    return DeviceRecord(**defaults)


@pytest.fixture
def sqlite_engine():
    """Moteur SQLite en memoire - simule l'interface PostgreSQL."""
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    yield engine
    engine.dispose()


@pytest.fixture
def session_factory(sqlite_engine):
    return sessionmaker(bind=sqlite_engine, autocommit=False, autoflush=False)


@pytest.fixture
def uow(session_factory):
    return SQLAlchemyUnitOfWork(session_factory)


class TestRepositoryInterface:
    def test_save_and_find_by_id(self, uow):
        record = make_record(
            device_id="d001", name="Thermostat",
            room_name="Salon", device_type="thermostat", manufacturer="Nest",
        )
        with uow:
            uow.devices.save(record)
            uow.commit()

        with uow:
            device = uow.devices.find_by_id("d001")
            assert device is not None
            assert device.name == "Thermostat"

    def test_find_all(self, uow):
        with uow:
            uow.devices.save(make_record(device_id="d1", name="A"))
            uow.devices.save(make_record(device_id="d2", name="B"))
            uow.commit()

        with uow:
            all_devices = uow.devices.find_all()
            assert len(all_devices) >= 2

    def test_find_by_type(self, uow):
        with uow:
            uow.devices.save(make_record(
                device_id="light1", name="Lampe",
                room_name="Chambre", device_type="light", manufacturer="Philips",  # noqa: E501
            ))
            uow.commit()

        with uow:
            lights = uow.devices.find_by_type("light")
            assert len(lights) >= 1
            assert all(d.device_type == "light" for d in lights)

    def test_find_by_room(self, uow):
        with uow:
            uow.devices.save(make_record(
                device_id="s1", name="Capteur",
                room_name="Cuisine", device_type="sensor", manufacturer="Generic",  # noqa: E501
            ))
            uow.commit()

        with uow:
            cuisine_devices = uow.devices.find_by_room("Cuisine")
            assert len(cuisine_devices) >= 1

    def test_delete(self, uow):
        with uow:
            uow.devices.save(make_record(device_id="del1", name="ToDelete"))
            uow.commit()

        with uow:
            uow.devices.delete("del1")
            uow.commit()

        with uow:
            assert uow.devices.find_by_id("del1") is None

    def test_count(self, uow):
        with uow:
            uow.devices.save(make_record(device_id="c1", name="X"))
            uow.devices.save(make_record(device_id="c2", name="Y"))
            uow.commit()

        with uow:
            count = uow.devices.count()
            assert count >= 2

    def test_rollback_on_error(self, uow):
        """Un rollback annule les modifications."""
        try:
            with uow:
                uow.devices.save(make_record(device_id="rb1", name="ToRollback"))  # noqa: E501
                raise RuntimeError("simulated error")
        except RuntimeError:
            pass

        with uow:
            device = uow.devices.find_by_id("rb1")
            assert device is None

    def test_repository_compatible_with_postgres_interface(self, session_factory):  # noqa: E501
        """Verifie que DeviceRepository expose l'interface attendue."""
        session = session_factory()
        repo = DeviceRepository(session)
        assert hasattr(repo, "save")
        assert hasattr(repo, "find_by_id")
        assert hasattr(repo, "find_all")
        assert hasattr(repo, "find_by_type")
        assert hasattr(repo, "find_by_room")
        assert hasattr(repo, "delete")
        assert hasattr(repo, "count")
        session.close()
