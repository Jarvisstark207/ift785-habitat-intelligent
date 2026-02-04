"""Tests unitaires pour les calculs statistiques"""

from application.services.stats_service import StatsService
from application.services.stats_advanced_service import StatsAdvancedService


class TestStatisticalCalculations:
    """Tests pour les calculs de statistiques"""

    def test_calculate_average_temperature(self, mock_repo):
        """Test calcul moyenne température"""
        mock_repo.get_average_temperature.return_value = 22.5

        service = StatsService(mock_repo)
        result = service.calculate_global_stats(["salon", "cuisine"])

        assert result["avg_temp"] == 22.5

    def test_calculate_total_consumption(self, mock_repo):
        """Test calcul consommation totale"""
        mock_repo.get_total_consumption.return_value = 450.0
        mock_repo.get_occupied_rooms_count.return_value = 2
        mock_repo.get_average_temperature.return_value = 22.0

        service = StatsService(mock_repo)
        result = service.calculate_global_stats(["salon", "cuisine", "chambre"])

        assert result["total_consumption"] == 450.0

    def test_calculate_location_stats_returns_all_metrics(self, mock_repo):
        """Test que calculate_location_stats retourne toutes les métriques"""
        mock_repo.get_stats_for_location.return_value = {
            "temp_avg": 22.0,
            "temp_min": 20.0,
            "temp_max": 24.0,
            "luminosity": 500,
            "movement": True,
            "consumption": 150.0,
        }

        service = StatsService(mock_repo)
        result = service.calculate_location_stats("salon")

        assert "temp_avg" in result
        assert "temp_min" in result
        assert "temp_max" in result
        assert "luminosity" in result
        assert "movement" in result
        assert "consumption" in result

    def test_hourly_stats_calculates_min_correctly(self, mock_repo):
        """Test calcul du minimum horaire"""
        mock_repo.find_with_filters.return_value = [
            {"timestamp": "2026-02-03T10:00:00", "value": 20.0},
            {"timestamp": "2026-02-03T10:15:00", "value": 18.5},
            {"timestamp": "2026-02-03T10:30:00", "value": 22.0},
        ]

        service = StatsAdvancedService(mock_repo)
        result = service.calculate_hourly_stats(date="2026-02-03")

        hourly = result["hourly_stats"][0]
        assert hourly["min"] == 18.5

    def test_hourly_stats_calculates_max_correctly(self, mock_repo):
        """Test calcul du maximum horaire"""
        mock_repo.find_with_filters.return_value = [
            {"timestamp": "2026-02-03T10:00:00", "value": 20.0},
            {"timestamp": "2026-02-03T10:15:00", "value": 25.5},
            {"timestamp": "2026-02-03T10:30:00", "value": 22.0},
        ]

        service = StatsAdvancedService(mock_repo)
        result = service.calculate_hourly_stats(date="2026-02-03")

        hourly = result["hourly_stats"][0]
        assert hourly["max"] == 25.5

    def test_hourly_stats_calculates_average_correctly(self, mock_repo):
        """Test calcul de la moyenne horaire"""
        mock_repo.find_with_filters.return_value = [
            {"timestamp": "2026-02-03T10:00:00", "value": 20.0},
            {"timestamp": "2026-02-03T10:15:00", "value": 22.0},
            {"timestamp": "2026-02-03T10:30:00", "value": 24.0},
        ]

        service = StatsAdvancedService(mock_repo)
        result = service.calculate_hourly_stats(date="2026-02-03")

        hourly = result["hourly_stats"][0]
        assert hourly["avg"] == 22.0  # (20 + 22 + 24) / 3

    def test_hourly_stats_counts_readings_correctly(self, mock_repo):
        """Test comptage des lectures horaires"""
        mock_repo.find_with_filters.return_value = [
            {"timestamp": "2026-02-03T10:00:00", "value": 20.0},
            {"timestamp": "2026-02-03T10:15:00", "value": 21.0},
            {"timestamp": "2026-02-03T10:30:00", "value": 22.0},
            {"timestamp": "2026-02-03T10:45:00", "value": 23.0},
        ]

        service = StatsAdvancedService(mock_repo)
        result = service.calculate_hourly_stats(date="2026-02-03")

        hourly = result["hourly_stats"][0]
        assert hourly["count"] == 4

    def test_occupied_rooms_count(self, mock_repo):
        """Test comptage des pièces occupées"""
        mock_repo.get_occupied_rooms_count.return_value = 3
        mock_repo.get_total_consumption.return_value = 300.0
        mock_repo.get_average_temperature.return_value = 22.0

        service = StatsService(mock_repo)
        result = service.calculate_global_stats(["salon", "cuisine", "chambre"])

        assert result["occupied_rooms"] == 3

    def test_stats_with_zero_values(self, mock_repo):
        """Test calculs avec valeurs zéro"""
        mock_repo.get_total_consumption.return_value = 0.0
        mock_repo.get_occupied_rooms_count.return_value = 0
        mock_repo.get_average_temperature.return_value = None

        service = StatsService(mock_repo)
        result = service.calculate_global_stats([])

        assert result["total_consumption"] == 0.0
        assert result["occupied_rooms"] == 0

    def test_temperature_range_calculation(self, mock_repo):
        """Test calcul de l'écart de température (max - min)"""
        mock_repo.get_stats_for_location.return_value = {
            "temp_avg": 22.0,
            "temp_min": 18.0,
            "temp_max": 26.0,
            "luminosity": 500,
            "movement": False,
            "consumption": 150.0,
        }

        service = StatsService(mock_repo)
        result = service.calculate_location_stats("salon")

        temp_range = result["temp_max"] - result["temp_min"]
        assert temp_range == 8.0
