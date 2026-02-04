"""Tests unitaires pour StatsService"""


class TestStatsService:
    """Tests pour le service de statistiques"""

    def test_calculate_location_stats_calls_repo(self, stats_service, mock_repo):
        """Test que calculate_location_stats appelle le repo"""

        mock_repo.get_stats_for_location.return_value = {
            "temp_avg": 22.0,
            "consumption": 150.0,
        }

        result = stats_service.calculate_location_stats("salon")

        mock_repo.get_stats_for_location.assert_called_once_with("salon")

        assert result["temp_avg"] == 22.0

        assert result["consumption"] == 150.0

    def test_calculate_global_stats_aggregates_data(self, stats_service, mock_repo):
        """Test calcul des stats globales"""

        mock_repo.get_total_consumption.return_value = 450.0

        mock_repo.get_occupied_rooms_count.return_value = 2

        mock_repo.get_average_temperature.return_value = 22.5

        locations = ["salon", "cuisine", "chambre"]

        result = stats_service.calculate_global_stats(locations)

        assert result["total_consumption"] == 450.0

        assert result["occupied_rooms"] == 2

        assert result["avg_temp"] == 22.5

        mock_repo.get_total_consumption.assert_called_once_with(locations)

        mock_repo.get_occupied_rooms_count.assert_called_once()

        mock_repo.get_average_temperature.assert_called_once_with(locations)

    def test_calculate_location_stats_returns_none_for_missing_data(self, stats_service, mock_repo):
        """Test gestion des données manquantes"""

        mock_repo.get_stats_for_location.return_value = {
            "temp_avg": None,
            "consumption": None,
        }

        result = stats_service.calculate_location_stats("inexistant")

        assert result["temp_avg"] is None

        assert result["consumption"] is None

    def test_stats_service_with_empty_locations(self, stats_service, mock_repo):
        """Test avec liste de locations vide"""

        mock_repo.get_total_consumption.return_value = 0.0

        mock_repo.get_occupied_rooms_count.return_value = 0

        mock_repo.get_average_temperature.return_value = None

        result = stats_service.calculate_global_stats([])

        assert result["total_consumption"] == 0.0

        assert result["occupied_rooms"] == 0
