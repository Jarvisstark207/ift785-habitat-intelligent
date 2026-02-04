"""Tests d'intégration pour les requêtes d'historique"""

import pytest
from datetime import datetime, timedelta
from infrastructure.db.sqlite_sensor_repo import SQLiteSensorRepository
from application.services.history_service import HistoryService
from application.services.stats_advanced_service import StatsAdvancedService
from domain.models.sensor_reading import SensorReading


class TestHistoryQueriesIntegration:
    """Tests d'intégration pour requêtes historique avec vraie DB"""

    @pytest.fixture(autouse=True)
    def setup_services(self, temp_db, monkeypatch):
        """Configure services avec DB temporaire"""
        monkeypatch.setattr("config.DB_NAME", temp_db)
        monkeypatch.setattr("infrastructure.db.sqlite_connection.DB_NAME", temp_db)

        self.repo = SQLiteSensorRepository()
        self.history_service = HistoryService(self.repo)
        self.stats_advanced_service = StatsAdvancedService(self.repo)

        # Insérer données de test
        self._populate_test_data()
        yield

    def _populate_test_data(self):
        """Peuple la DB avec données de test"""
        base_time = datetime.now().replace(hour=10, minute=0, second=0, microsecond=0)

        locations = ["salon", "cuisine", "chambre"]
        types = ["temperature", "lumiere", "consommation"]

        for location in locations:
            for sensor_type in types:
                for i in range(24):  # 24 heures
                    timestamp = (base_time - timedelta(hours=i)).isoformat()
                    reading = SensorReading(
                        sensor_id=f"{sensor_type}_{location}_{i}",
                        location=location,
                        type=sensor_type,
                        value=20.0 + i * 0.5 if sensor_type == "temperature" else 100.0 + i * 10,
                        unit="°C" if sensor_type == "temperature" else "unit",
                        timestamp=timestamp,
                    )
                    self.repo.save(reading)

    def test_query_history_by_location(self):
        """Test requête historique par location"""
        result = self.history_service.get_filtered_history(location="salon")

        assert result["count"] > 0
        for item in result["data"]:
            assert item["location"] == "salon"

    def test_query_history_by_sensor_type(self):
        """Test requête historique par type de capteur"""
        result = self.history_service.get_filtered_history(sensor_type="temperature")

        assert result["count"] > 0
        for item in result["data"]:
            assert item["type"] == "temperature"

    def test_query_history_by_date_range(self):
        base_time = datetime.now().replace(hour=10, minute=0, second=0, microsecond=0)

        start = (base_time - timedelta(hours=12)).isoformat()
        end = base_time.isoformat()

        result = self.history_service.get_filtered_history(start_date=start, end_date=end)

        assert result["count"] > 0

    def test_query_history_with_limit(self):
        """Test requête historique avec limite"""
        result = self.history_service.get_filtered_history(limit=10)

        assert result["count"] <= 10
        assert len(result["data"]) <= 10

    def test_query_history_combined_filters(self):
        """Test requête avec filtres combinés"""
        now = datetime.now()
        start = (now - timedelta(hours=6)).isoformat()

        result = self.history_service.get_filtered_history(
            location="salon", sensor_type="temperature", start_date=start, limit=5
        )

        assert result["count"] <= 5
        for item in result["data"]:
            assert item["location"] == "salon"
            assert item["type"] == "temperature"

    def test_query_hourly_stats_full_day(self):
        """Test stats horaires pour journée complète"""
        today = datetime.now().strftime("%Y-%m-%d")

        result = self.stats_advanced_service.calculate_hourly_stats(
            location="salon", sensor_type="temperature", date=today
        )

        assert "hourly_stats" in result
        assert len(result["hourly_stats"]) > 0

    def test_query_hourly_stats_specific_location(self):
        """Test stats horaires pour location spécifique"""
        today = datetime.now().strftime("%Y-%m-%d")

        result = self.stats_advanced_service.calculate_hourly_stats(
            location="cuisine", sensor_type="temperature", date=today
        )

        assert result["location"] == "cuisine"
        assert result["sensor_type"] == "temperature"

    def test_query_empty_results(self):
        """Test requête retournant résultats vides"""
        result = self.history_service.get_filtered_history(
            location="inexistant", sensor_type="temperature"
        )

        assert result["count"] == 0
        assert len(result["data"]) == 0

    def test_query_performance_large_dataset(self):
        """Test performance sur grand dataset"""
        import time

        start_time = time.time()
        result = self.history_service.get_filtered_history(limit=100)
        elapsed = time.time() - start_time

        # Devrait prendre moins d'une seconde
        assert elapsed < 1.0
        assert result["count"] > 0

    def test_query_history_order_by_timestamp(self):
        """Test que l'historique est trié par timestamp DESC"""
        result = self.history_service.get_filtered_history(
            location="salon", sensor_type="temperature", limit=10
        )

        if len(result["data"]) > 1:
            timestamps = [item["timestamp"] for item in result["data"]]
            # Vérifier ordre décroissant
            assert timestamps == sorted(timestamps, reverse=True)
