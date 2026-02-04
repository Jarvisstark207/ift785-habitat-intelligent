"""Tests unitaires pour StatsAdvancedService"""

from datetime import datetime

class TestStatsAdvancedService:
    """Tests pour le service de statistiques avancées"""

    def test_calculate_hourly_stats_uses_today_if_no_date(self, stats_advanced_service, mock_repo):
        """Test utilise date du jour si aucune date fournie"""

        mock_repo.find_with_filters.return_value = []

        stats_advanced_service.calculate_hourly_stats()

        today = datetime.now().strftime("%Y-%m-%d")

        mock_repo.find_with_filters.assert_called_once()

        # Vérifier que start_date commence par la date du jour

        call_args = mock_repo.find_with_filters.call_args[1]

        assert call_args["start_date"].startswith(today)

    def test_calculate_hourly_stats_groups_by_hour(self, stats_advanced_service, mock_repo):
        """Test groupement des données par heure"""

        mock_data = [
            {"timestamp": "2026-02-03T10:15:00", "value": 22.0},
            {"timestamp": "2026-02-03T10:30:00", "value": 22.5},
            {"timestamp": "2026-02-03T11:00:00", "value": 23.0},
            {"timestamp": "2026-02-03T11:15:00", "value": 23.5},
        ]

        mock_repo.find_with_filters.return_value = mock_data

        result = stats_advanced_service.calculate_hourly_stats(
            location="salon", sensor_type="temperature", date="2026-02-03"
        )

        assert "hourly_stats" in result

        assert len(result["hourly_stats"]) == 2  # 2 heures différentes

    def test_calculate_hourly_stats_computes_avg_min_max(self, stats_advanced_service, mock_repo):
        """Test calcul avg, min, max pour chaque heure"""

        mock_data = [
            {"timestamp": "2026-02-03T10:00:00", "value": 20.0},
            {"timestamp": "2026-02-03T10:15:00", "value": 22.0},
            {"timestamp": "2026-02-03T10:30:00", "value": 24.0},
        ]

        mock_repo.find_with_filters.return_value = mock_data

        result = stats_advanced_service.calculate_hourly_stats(date="2026-02-03")

        hourly = result["hourly_stats"][0]

        assert "avg" in hourly

        assert "min" in hourly

        assert "max" in hourly

        assert "count" in hourly

        assert hourly["avg"] == 22.0

        assert hourly["min"] == 20.0

        assert hourly["max"] == 24.0

        assert hourly["count"] == 3

    def test_calculate_hourly_stats_with_location_filter(self, stats_advanced_service, mock_repo):
        """Test filtrage par location"""

        mock_repo.find_with_filters.return_value = []

        result = stats_advanced_service.calculate_hourly_stats(
            location="cuisine", date="2026-02-03"
        )

        assert result["location"] == "cuisine"

        call_args = mock_repo.find_with_filters.call_args[1]

        assert call_args["location"] == "cuisine"

    def test_calculate_hourly_stats_with_sensor_type_filter(
        self, stats_advanced_service, mock_repo
    ):
        """Test filtrage par type de capteur"""

        mock_repo.find_with_filters.return_value = []

        result = stats_advanced_service.calculate_hourly_stats(
            sensor_type="consommation", date="2026-02-03"
        )

        assert result["sensor_type"] == "consommation"

        call_args = mock_repo.find_with_filters.call_args[1]

        assert call_args["sensor_type"] == "consommation"

    def test_calculate_hourly_stats_returns_empty_for_no_data(
        self, stats_advanced_service, mock_repo
    ):
        """Test retour vide si pas de données"""

        mock_repo.find_with_filters.return_value = []

        result = stats_advanced_service.calculate_hourly_stats(date="2026-02-03")

        assert result["hourly_stats"] == []

    def test_calculate_hourly_stats_sorts_hours(self, stats_advanced_service, mock_repo):
        """Test que les heures sont triées"""

        mock_data = [
            {"timestamp": "2026-02-03T14:00:00", "value": 22.0},
            {"timestamp": "2026-02-03T10:00:00", "value": 20.0},
            {"timestamp": "2026-02-03T12:00:00", "value": 21.0},
        ]

        mock_repo.find_with_filters.return_value = mock_data

        result = stats_advanced_service.calculate_hourly_stats(date="2026-02-03")

        hours = [h["hour"] for h in result["hourly_stats"]]

        assert hours == sorted(hours)
