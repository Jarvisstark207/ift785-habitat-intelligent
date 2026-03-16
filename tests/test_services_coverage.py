"""Tests pour améliorer la couverture des services et de main.py"""
import pytest
from unittest.mock import MagicMock, patch
from domain.models.sensor_reading import SensorReading
from application.services.stats_service import StatsService
from application.services.alert_service import AlertService
from application.services.dashboard_service import DashboardService
from application.use_cases.ingest_sensor_reading import IngestSensorReading


# ─── Fixtures ────────────────────────────────────────────────────────────────

@pytest.fixture
def repo_mock():
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
    repo.get_occupied_rooms_count.return_value = 2
    repo.get_average_temperature.return_value = 21.0
    repo.find_recent.return_value = [{"sensor_id": "s1"}]
    repo.find_temperature_history.return_value = {"salon": []}
    repo.find_consumption_current.return_value = {"salon": 100.0}
    return repo


# ─── Tests AlertService – branches manquantes ─────────────────────────────────

class TestAlertServiceBranches:

    def test_alerte_temperature_basse(self, repo_mock):
        repo_mock.get_stats_for_location.return_value = {
            'temp_avg': 10.0,
            'temp_min': 8.0,
            'temp_max': 12.0,
            'luminosity': None,
            'movement': False,
            'consumption': 100.0
        }
        repo_mock.get_total_consumption.return_value = 100.0

        stats = StatsService(repo_mock)
        alert = AlertService(stats)

        with patch('application.services.alert_service.ALERT_TEMP_MIN', 15.0), \
             patch('application.services.alert_service.ALERT_TEMP_MAX', 30.0), \
             patch('application.services.alert_service.ALERT_CONSUMPTION_MAX', 5000.0):
            alertes = alert.generate_alerts(["salon"])

        assert any("basse" in a.lower() for a in alertes)

    def test_alerte_consommation_elevee(self, repo_mock):
        repo_mock.get_total_consumption.return_value = 9000.0

        stats = StatsService(repo_mock)
        alert = AlertService(stats)

        with patch('application.services.alert_service.ALERT_TEMP_MIN', 15.0), \
             patch('application.services.alert_service.ALERT_TEMP_MAX', 30.0), \
             patch('application.services.alert_service.ALERT_CONSUMPTION_MAX', 5000.0):
            alertes = alert.generate_alerts(["salon"])

        assert any("consommation" in a.lower() for a in alertes)

    def test_pas_alerte_temp_avg_none(self, repo_mock):
        repo_mock.get_stats_for_location.return_value = {
            'temp_avg': None,
            'luminosity': None,
            'movement': False,
            'consumption': None
        }
        repo_mock.get_total_consumption.return_value = 100.0

        stats = StatsService(repo_mock)
        alert = AlertService(stats)

        with patch('application.services.alert_service.ALERT_TEMP_MIN', 15.0), \
             patch('application.services.alert_service.ALERT_TEMP_MAX', 30.0), \
             patch('application.services.alert_service.ALERT_CONSUMPTION_MAX', 5000.0):
            alertes = alert.generate_alerts(["salon"])

        assert alertes == []

    def test_alertes_plusieurs_locations(self, repo_mock):
        repo_mock.get_stats_for_location.side_effect = [
            {'temp_avg': 35.0, 'temp_min': 30.0, 'temp_max': 38.0,
             'luminosity': None, 'movement': False, 'consumption': 100.0},
            {'temp_avg': 10.0, 'temp_min': 8.0, 'temp_max': 12.0,
             'luminosity': None, 'movement': False, 'consumption': 50.0},
        ]
        repo_mock.get_total_consumption.return_value = 150.0

        stats = StatsService(repo_mock)
        alert = AlertService(stats)

        with patch('application.services.alert_service.ALERT_TEMP_MIN', 15.0), \
             patch('application.services.alert_service.ALERT_TEMP_MAX', 30.0), \
             patch('application.services.alert_service.ALERT_CONSUMPTION_MAX', 5000.0):
            alertes = alert.generate_alerts(["salon", "cuisine"])

        assert len(alertes) == 2


# ─── Tests StatsService ───────────────────────────────────────────────────────

class TestStatsServiceComplet:

    def test_calculate_global_stats_structure(self, repo_mock):
        stats = StatsService(repo_mock)
        result = stats.calculate_global_stats(["salon", "cuisine"])

        assert "total_consumption" in result
        assert "occupied_rooms" in result
        assert "avg_temp" in result
        assert result["total_consumption"] == 300.0
        assert result["occupied_rooms"] == 2
        assert result["avg_temp"] == 21.0

    def test_calculate_location_stats_delegue_repo(self, repo_mock):
        stats = StatsService(repo_mock)
        result = stats.calculate_location_stats("salon")
        repo_mock.get_stats_for_location.assert_called_once_with("salon")
        assert result["temp_avg"] == 22.5


# ─── Tests DashboardService – branches ───────────────────────────────────────

class TestDashboardServiceComplet:

    def test_get_dashboard_data_plusieurs_locations(self, repo_mock):
        stats = StatsService(repo_mock)
        alert = AlertService(stats)
        dashboard = DashboardService(repo_mock, stats, alert)

        with patch('application.services.alert_service.ALERT_TEMP_MIN', 15.0), \
             patch('application.services.alert_service.ALERT_TEMP_MAX', 30.0), \
             patch('application.services.alert_service.ALERT_CONSUMPTION_MAX', 5000.0):
            data = dashboard.get_dashboard_data(["salon", "cuisine", "chambre"])

        assert "salon" in data["locations"]
        assert "cuisine" in data["locations"]
        assert "chambre" in data["locations"]
        assert data["recent"] == [{"sensor_id": "s1"}]
        assert data["temperature_history"] == {"salon": []}

    def test_get_dashboard_data_appelle_repo(self, repo_mock):
        stats = StatsService(repo_mock)
        alert = AlertService(stats)
        dashboard = DashboardService(repo_mock, stats, alert)

        with patch('application.services.alert_service.ALERT_TEMP_MIN', 15.0), \
             patch('application.services.alert_service.ALERT_TEMP_MAX', 30.0), \
             patch('application.services.alert_service.ALERT_CONSUMPTION_MAX', 5000.0):
            dashboard.get_dashboard_data(["salon"])

        repo_mock.find_recent.assert_called_once_with(20)
        repo_mock.find_temperature_history.assert_called_once_with(["salon"])
        repo_mock.find_consumption_current.assert_called_once_with(["salon"])


# ─── Tests IngestSensorReading ────────────────────────────────────────────────

class TestIngestSensorReadingComplet:

    def test_execute_affiche_log(self, capsys):
        repo = MagicMock()
        use_case = IngestSensorReading(repo)
        reading = SensorReading("s1", "salon", "temperature", 22.5, "C",
                                "2024-01-01T10:00:00")
        use_case.execute(reading)
        captured = capsys.readouterr()
        assert "salon" in captured.out
        assert "temperature" in captured.out

    def test_execute_retourne_none(self):
        repo = MagicMock()
        use_case = IngestSensorReading(repo)
        reading = SensorReading("s1", "salon", "temperature", 22.5, "C",
                                "2024-01-01T10:00:00")
        result = use_case.execute(reading)
        assert result is None


# ─── Tests app/main.py ────────────────────────────────────────────────────────

class TestCreateApp:

    def test_create_app_retourne_fastapi(self):
        from fastapi import FastAPI
        from infrastructure.db.sqlite_sensor_repo import SQLiteSensorRepository

        mock_repo = MagicMock(spec=SQLiteSensorRepository)

        with patch(
            "app.main.SQLiteSensorRepository",
            return_value=mock_repo
        ), patch("app.main.setup_routes"):
            from app.main import create_app
            app, repo = create_app()

        assert isinstance(app, FastAPI)
        assert repo is mock_repo

    def test_start_sensor_listener_demarre_thread(self):
        mock_repo = MagicMock()
        mock_source = MagicMock()
        mock_thread = MagicMock()

        with patch(
            "app.main.HabitatClientSource", return_value=mock_source
        ), patch(
            "threading.Thread", return_value=mock_thread
        ):
            from app.main import start_sensor_listener
            start_sensor_listener(mock_repo)

        mock_thread.start.assert_called_once()
