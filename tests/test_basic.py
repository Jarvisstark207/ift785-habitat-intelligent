"""Tests de base : SensorReading, services et use cases"""
import pytest
from unittest.mock import MagicMock, patch
from domain.models.sensor_reading import SensorReading
from application.services.stats_service import StatsService
from application.services.alert_service import AlertService
from application.services.dashboard_service import DashboardService
from application.use_cases.ingest_sensor_reading import IngestSensorReading


# ─── Fixtures ────────────────────────────────────────────────────────────────

@pytest.fixture
def lecture():
    return SensorReading(
        sensor_id="s1",
        location="salon",
        type="temperature",
        value=22.5,
        unit="C",
        timestamp="2024-01-01T10:00:00"
    )


@pytest.fixture
def repo_mock():
    """Repository SQLite simulé"""
    repo = MagicMock()
    repo.get_stats_for_location.return_value = {
        'temp_avg': 22.5,
        'temp_min': 20.0,
        'temp_max': 25.0,
        'luminosity': 300,
        'movement': False,
        'consumption': 150.0
    }
    repo.get_total_consumption.return_value = 300.0
    repo.get_occupied_rooms_count.return_value = 1
    repo.get_average_temperature.return_value = 22.5
    repo.find_recent.return_value = []
    repo.find_temperature_history.return_value = {}
    repo.find_consumption_current.return_value = {}
    return repo


# ─── Tests SensorReading ─────────────────────────────────────────────────────

class TestSensorReading:

    def test_creation(self, lecture):
        assert lecture.sensor_id == "s1"
        assert lecture.location == "salon"
        assert lecture.type == "temperature"
        assert lecture.value == 22.5
        assert lecture.unit == "C"

    def test_to_db_tuple(self, lecture):
        t = lecture.to_db_tuple()
        assert t == ("s1", "salon", "temperature", 22.5, "C", "2024-01-01T10:00:00")

    def test_to_dict(self, lecture):
        d = lecture.to_dict()
        assert d["sensor_id"] == "s1"
        assert d["location"] == "salon"
        assert d["type"] == "temperature"
        assert d["value"] == 22.5
        assert d["unit"] == "C"
        assert d["timestamp"] == "2024-01-01T10:00:00"

    def test_immutable(self, lecture):
        with pytest.raises(AttributeError):
            setattr(lecture, 'value', 99.0)

    def test_from_sensor_data(self):
        sensor_data = MagicMock()
        sensor_data.sensor_id = "s99"
        sensor_data.location = "cuisine"
        sensor_data.type = "lumiere"
        sensor_data.value = 500
        sensor_data.unit = "lux"
        sensor_data.timestamp = "2024-01-01T12:00:00"

        reading = SensorReading.from_sensor_data(sensor_data)
        assert reading.sensor_id == "s99"
        assert reading.location == "cuisine"
        assert reading.type == "lumiere"
        assert reading.value == 500


# ─── Tests StatsService ───────────────────────────────────────────────────────

class TestStatsService:

    def test_calculate_location_stats(self, repo_mock):
        service = StatsService(repo_mock)
        stats = service.calculate_location_stats("salon")
        repo_mock.get_stats_for_location.assert_called_once_with("salon")
        assert stats['temp_avg'] == 22.5

    def test_calculate_global_stats(self, repo_mock):
        service = StatsService(repo_mock)
        result = service.calculate_global_stats(["salon", "cuisine"])
        assert result['total_consumption'] == 300.0
        assert result['occupied_rooms'] == 1
        assert result['avg_temp'] == 22.5


# ─── Tests AlertService ───────────────────────────────────────────────────────

class TestAlertService:

    def test_alerte_temperature_elevee(self, repo_mock):
        repo_mock.get_stats_for_location.return_value = {
            'temp_avg': 35.0,
            'temp_min': 30.0,
            'temp_max': 38.0,
            'luminosity': None,
            'movement': False,
            'consumption': 100.0
        }
        repo_mock.get_total_consumption.return_value = 100.0

        stats_service = StatsService(repo_mock)
        alert_service = AlertService(stats_service)

        with patch('application.services.alert_service.ALERT_TEMP_MAX', 30.0), \
             patch('application.services.alert_service.ALERT_TEMP_MIN', 15.0), \
             patch('application.services.alert_service.ALERT_CONSUMPTION_MAX', 5000.0):
            alertes = alert_service.generate_alerts(["salon"])

        assert any("elevee" in a.lower() or "Temperature" in a for a in alertes)

    def test_pas_d_alerte_normale(self, repo_mock):
        stats_service = StatsService(repo_mock)
        alert_service = AlertService(stats_service)

        with patch('application.services.alert_service.ALERT_TEMP_MAX', 30.0), \
             patch('application.services.alert_service.ALERT_TEMP_MIN', 15.0), \
             patch('application.services.alert_service.ALERT_CONSUMPTION_MAX', 5000.0):
            alertes = alert_service.generate_alerts(["salon"])

        assert alertes == []


# ─── Tests IngestSensorReading ────────────────────────────────────────────────

class TestIngestSensorReading:

    def test_execute_appelle_save(self, lecture):
        repo = MagicMock()
        use_case = IngestSensorReading(repo)
        use_case.execute(lecture)
        repo.save.assert_called_once_with(lecture)

    def test_execute_plusieurs_lectures(self):
        repo = MagicMock()
        use_case = IngestSensorReading(repo)

        l1 = SensorReading("s1", "salon", "temperature", 20.0, "C", "2024-01-01T10:00:00")
        l2 = SensorReading("s2", "cuisine", "lumiere", 400, "lux", "2024-01-01T10:01:00")

        use_case.execute(l1)
        use_case.execute(l2)

        assert repo.save.call_count == 2


# ─── Tests DashboardService ───────────────────────────────────────────────────

class TestDashboardService:

    def test_get_dashboard_data_structure(self, repo_mock):
        stats_service = StatsService(repo_mock)
        alert_service = AlertService(stats_service)
        dashboard = DashboardService(repo_mock, stats_service, alert_service)

        with patch('application.services.alert_service.ALERT_TEMP_MAX', 30.0), \
             patch('application.services.alert_service.ALERT_TEMP_MIN', 15.0), \
             patch('application.services.alert_service.ALERT_CONSUMPTION_MAX', 5000.0):
            data = dashboard.get_dashboard_data(["salon"])

        assert "global" in data
        assert "locations" in data
        assert "alerts" in data
        assert "recent" in data
        assert "temperature_history" in data
        assert "consumption_current" in data
