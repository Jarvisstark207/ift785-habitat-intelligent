"""
Tests unitaires pour le Unit of Work Pattern - Iteration 6
"""

import pytest
from unittest.mock import MagicMock
from infrastructure.db.unit_of_work import SQLAlchemyUnitOfWork
from infrastructure.db.device_repository import DeviceRepository
from infrastructure.db.sqlalchemy_models import DeviceRecord


@pytest.fixture
def mock_session():
    return MagicMock()


@pytest.fixture
def mock_session_factory(mock_session):
    factory = MagicMock(return_value=mock_session)
    return factory


class TestSQLAlchemyUnitOfWorkContext:
    def test_enter_creates_session_and_repository(self, mock_session_factory, mock_session):
        uow = SQLAlchemyUnitOfWork(mock_session_factory)
        result = uow.__enter__()
        assert result is uow
        assert uow.session is mock_session
        assert isinstance(uow.devices, DeviceRepository)

    def test_exit_closes_session_on_success(self, mock_session_factory, mock_session):
        uow = SQLAlchemyUnitOfWork(mock_session_factory)
        uow.__enter__()
        uow.__exit__(None, None, None)
        mock_session.close.assert_called_once()

    def test_exit_rollbacks_on_exception(self, mock_session_factory, mock_session):
        uow = SQLAlchemyUnitOfWork(mock_session_factory)
        uow.__enter__()
        uow.__exit__(ValueError, ValueError("error"), None)
        mock_session.rollback.assert_called_once()
        mock_session.close.assert_called_once()

    def test_context_manager_usage(self, mock_session_factory, mock_session):
        with SQLAlchemyUnitOfWork(mock_session_factory) as uow:
            assert uow.session is mock_session
        mock_session.close.assert_called_once()


class TestSQLAlchemyUnitOfWorkCommit:
    def test_commit_calls_session_commit(self, mock_session_factory, mock_session):
        uow = SQLAlchemyUnitOfWork(mock_session_factory)
        uow.__enter__()
        uow.commit()
        mock_session.commit.assert_called_once()

    def test_multiple_commits(self, mock_session_factory, mock_session):
        uow = SQLAlchemyUnitOfWork(mock_session_factory)
        uow.__enter__()
        uow.commit()
        uow.commit()
        assert mock_session.commit.call_count == 2


class TestSQLAlchemyUnitOfWorkRollback:
    def test_rollback_calls_session_rollback(self, mock_session_factory, mock_session):
        uow = SQLAlchemyUnitOfWork(mock_session_factory)
        uow.__enter__()
        uow.rollback()
        mock_session.rollback.assert_called_once()

    def test_rollback_after_save(self, mock_session_factory, mock_session):
        mock_session.query.return_value.filter_by.return_value.first.return_value = None
        with SQLAlchemyUnitOfWork(mock_session_factory) as uow:
            device = DeviceRecord(device_id="d1", name="Test")
            uow.devices.save(device)
            uow.rollback()
        mock_session.rollback.assert_called()


class TestSQLAlchemyUnitOfWorkAtomicity:
    def test_exception_triggers_rollback(self, mock_session_factory, mock_session):
        try:
            with SQLAlchemyUnitOfWork(mock_session_factory):
                raise RuntimeError("simulated error")
        except RuntimeError:
            pass
        mock_session.rollback.assert_called()

    def test_no_rollback_on_success(self, mock_session_factory, mock_session):
        with SQLAlchemyUnitOfWork(mock_session_factory) as uow:
            uow.commit()
        mock_session.rollback.assert_not_called()

    def test_devices_repository_available(self, mock_session_factory):
        with SQLAlchemyUnitOfWork(mock_session_factory) as uow:
            assert uow.devices is not None
            assert isinstance(uow.devices, DeviceRepository)
