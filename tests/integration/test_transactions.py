"""
Tests d'integration pour les transactions et Unit of Work - Iteration 6
"""

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from infrastructure.db.sqlalchemy_models import Base, DeviceRecord
from infrastructure.db.unit_of_work import SQLAlchemyUnitOfWork


@pytest.fixture
def session_factory():
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    factory = sessionmaker(bind=engine)
    yield factory
    engine.dispose()


class TestUnitOfWorkCommit:
    def test_commit_persists_data(self, session_factory):
        with SQLAlchemyUnitOfWork(session_factory) as uow:
            uow.devices.save(DeviceRecord(device_id="c1", name="Committed"))
            uow.commit()

        with SQLAlchemyUnitOfWork(session_factory) as uow:
            found = uow.devices.find_by_id("c1")
            assert found is not None
            assert found.name == "Committed"

    def test_commit_multiple_devices(self, session_factory):
        with SQLAlchemyUnitOfWork(session_factory) as uow:
            for i in range(4):
                uow.devices.save(DeviceRecord(device_id=f"m{i}", name=f"Multi {i}"))
            uow.commit()

        with SQLAlchemyUnitOfWork(session_factory) as uow:
            assert uow.devices.count() == 4


class TestUnitOfWorkRollback:
    def test_explicit_rollback_does_not_persist(self, session_factory):
        with SQLAlchemyUnitOfWork(session_factory) as uow:
            uow.devices.save(DeviceRecord(device_id="r1", name="Rolled Back"))
            uow.rollback()

        with SQLAlchemyUnitOfWork(session_factory) as uow:
            found = uow.devices.find_by_id("r1")
            assert found is None

    def test_exception_triggers_automatic_rollback(self, session_factory):
        try:
            with SQLAlchemyUnitOfWork(session_factory) as uow:
                uow.devices.save(DeviceRecord(device_id="e1", name="Exception Device"))
                raise RuntimeError("forced error")
        except RuntimeError:
            pass

        with SQLAlchemyUnitOfWork(session_factory) as uow:
            found = uow.devices.find_by_id("e1")
            assert found is None

    def test_partial_batch_rollback(self, session_factory):
        try:
            with SQLAlchemyUnitOfWork(session_factory) as uow:
                uow.devices.save(DeviceRecord(device_id="p1", name="Partial 1"))
                uow.devices.save(DeviceRecord(device_id="p2", name="Partial 2"))
                raise ValueError("batch error")
        except ValueError:
            pass

        with SQLAlchemyUnitOfWork(session_factory) as uow:
            assert uow.devices.find_by_id("p1") is None
            assert uow.devices.find_by_id("p2") is None


class TestUnitOfWorkIsolation:
    def test_two_separate_transactions(self, session_factory):
        with SQLAlchemyUnitOfWork(session_factory) as uow:
            uow.devices.save(DeviceRecord(device_id="tx1", name="Trans 1"))
            uow.commit()

        with SQLAlchemyUnitOfWork(session_factory) as uow:
            uow.devices.save(DeviceRecord(device_id="tx2", name="Trans 2"))
            uow.commit()

        with SQLAlchemyUnitOfWork(session_factory) as uow:
            assert uow.devices.count() == 2

    def test_rollback_does_not_affect_committed(self, session_factory):
        with SQLAlchemyUnitOfWork(session_factory) as uow:
            uow.devices.save(DeviceRecord(device_id="safe", name="Safe Device"))
            uow.commit()

        try:
            with SQLAlchemyUnitOfWork(session_factory) as uow:
                uow.devices.save(DeviceRecord(device_id="unsafe", name="Unsafe"))
                raise RuntimeError("rollback this")
        except RuntimeError:
            pass

        with SQLAlchemyUnitOfWork(session_factory) as uow:
            assert uow.devices.find_by_id("safe") is not None
            assert uow.devices.find_by_id("unsafe") is None
            assert uow.devices.count() == 1


class TestUnitOfWorkBatchOperations:
    def test_batch_insert_all_or_nothing(self, session_factory):
        devices_data = [
            {"device_id": "b1", "name": "Batch 1"},
            {"device_id": "b2", "name": "Batch 2"},
            {"device_id": "b3", "name": "Batch 3"},
        ]

        with SQLAlchemyUnitOfWork(session_factory) as uow:
            for d in devices_data:
                uow.devices.save(DeviceRecord(**d))
            uow.commit()

        with SQLAlchemyUnitOfWork(session_factory) as uow:
            assert uow.devices.count() == 3

    def test_batch_rollback_leaves_db_empty(self, session_factory):
        try:
            with SQLAlchemyUnitOfWork(session_factory) as uow:
                uow.devices.save(DeviceRecord(device_id="br1", name="Batch Rollback 1"))
                uow.devices.save(DeviceRecord(device_id="br2", name="Batch Rollback 2"))
                raise Exception("batch failed")
        except Exception:
            pass

        with SQLAlchemyUnitOfWork(session_factory) as uow:
            assert uow.devices.count() == 0
