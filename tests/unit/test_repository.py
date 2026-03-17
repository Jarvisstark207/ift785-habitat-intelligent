"""
Tests unitaires pour le Repository Pattern - Iteration 6
"""

import pytest
from unittest.mock import MagicMock, patch
from infrastructure.db.device_repository import DeviceRepository
from infrastructure.db.sqlalchemy_models import DeviceRecord


@pytest.fixture
def mock_session():
    return MagicMock()


@pytest.fixture
def repository(mock_session):
    return DeviceRepository(mock_session)


@pytest.fixture
def sample_device():
    return DeviceRecord(
        device_id="dev-001",
        name="Lampe Salon",
        room_name="salon",
        device_type="light",
        manufacturer="Philips",
        status="active",
    )


class TestDeviceRepositorySave:
    def test_save_new_device(self, repository, mock_session, sample_device):
        mock_session.query.return_value.filter_by.return_value.first.return_value = None
        result = repository.save(sample_device)
        mock_session.add.assert_called_once_with(sample_device)
        assert result == sample_device

    def test_save_existing_device_updates_fields(self, repository, mock_session, sample_device):
        existing = DeviceRecord(
            device_id="dev-001",
            name="Old Name",
            room_name="cuisine",
            device_type="thermostat",
            manufacturer="Nest",
            status="inactive",
        )
        mock_session.query.return_value.filter_by.return_value.first.return_value = existing
        updated = DeviceRecord(
            device_id="dev-001",
            name="New Name",
            room_name="salon",
            device_type="light",
            manufacturer="Philips",
            status="active",
        )
        result = repository.save(updated)
        assert result.name == "New Name"
        assert result.room_name == "salon"
        mock_session.add.assert_not_called()


class TestDeviceRepositoryFind:
    def test_find_by_id_existing(self, repository, mock_session, sample_device):
        mock_session.query.return_value.filter_by.return_value.first.return_value = sample_device
        result = repository.find_by_id("dev-001")
        assert result == sample_device

    def test_find_by_id_missing(self, repository, mock_session):
        mock_session.query.return_value.filter_by.return_value.first.return_value = None
        result = repository.find_by_id("inexistant")
        assert result is None

    def test_find_all(self, repository, mock_session, sample_device):
        mock_session.query.return_value.all.return_value = [sample_device]
        result = repository.find_all()
        assert len(result) == 1
        assert result[0] == sample_device

    def test_find_all_empty(self, repository, mock_session):
        mock_session.query.return_value.all.return_value = []
        result = repository.find_all()
        assert result == []

    def test_find_by_type(self, repository, mock_session, sample_device):
        mock_session.query.return_value.filter_by.return_value.all.return_value = [sample_device]
        result = repository.find_by_type("light")
        assert len(result) == 1

    def test_find_by_room(self, repository, mock_session, sample_device):
        mock_session.query.return_value.filter_by.return_value.all.return_value = [sample_device]
        result = repository.find_by_room("salon")
        assert len(result) == 1


class TestDeviceRepositoryDelete:
    def test_delete_existing_device(self, repository, mock_session, sample_device):
        mock_session.query.return_value.filter_by.return_value.first.return_value = sample_device
        result = repository.delete("dev-001")
        assert result is True
        mock_session.delete.assert_called_once_with(sample_device)

    def test_delete_nonexistent_device(self, repository, mock_session):
        mock_session.query.return_value.filter_by.return_value.first.return_value = None
        result = repository.delete("inexistant")
        assert result is False
        mock_session.delete.assert_not_called()


class TestDeviceRepositoryCount:
    def test_count(self, repository, mock_session):
        mock_session.query.return_value.count.return_value = 5
        result = repository.count()
        assert result == 5

    def test_count_empty(self, repository, mock_session):
        mock_session.query.return_value.count.return_value = 0
        result = repository.count()
        assert result == 0


class TestDeviceRecord:
    def test_to_dict(self, sample_device):
        d = sample_device.to_dict()
        assert d["device_id"] == "dev-001"
        assert d["name"] == "Lampe Salon"
        assert d["room_name"] == "salon"
        assert d["device_type"] == "light"
        assert d["manufacturer"] == "Philips"
        assert d["status"] == "active"

    def test_device_record_defaults(self):
        device = DeviceRecord(device_id="x", name="Test")
        assert device.device_id == "x"
        assert device.name == "Test"
        # SQLAlchemy column defaults applied at DB level, not at object creation
        assert device.room_name is None or device.room_name == ""
        assert device.status is None or device.status == "active"
