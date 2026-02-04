"""Tests unitaires pour HistoryService"""


class TestHistoryService:
    """Tests pour le service d'historique"""

    def test_get_filtered_history_calls_repo_with_all_params(self, history_service, mock_repo):
        """Test que get_filtered_history passe tous les paramètres au repo"""

        mock_repo.find_with_filters.return_value = []

        history_service.get_filtered_history(
            location="salon",
            sensor_type="temperature",
            start_date="2026-01-01T00:00:00",
            end_date="2026-01-31T23:59:59",
            limit=50,
        )

        mock_repo.find_with_filters.assert_called_once_with(
            location="salon",
            sensor_type="temperature",
            start_date="2026-01-01T00:00:00",
            end_date="2026-01-31T23:59:59",
            limit=50,
        )

    def test_get_filtered_history_returns_correct_structure(self, history_service, mock_repo):
        """Test structure de retour de get_filtered_history"""

        mock_data = [
            {"sensor_id": "t1", "location": "salon", "value": 22.0},
            {"sensor_id": "t2", "location": "salon", "value": 22.5},
        ]

        mock_repo.find_with_filters.return_value = mock_data

        result = history_service.get_filtered_history(location="salon")

        assert "count" in result

        assert "filters" in result

        assert "data" in result

        assert result["count"] == 2

        assert result["data"] == mock_data

    def test_get_filtered_history_with_no_filters(self, history_service, mock_repo):
        """Test sans filtres (tous None)"""

        mock_repo.find_with_filters.return_value = []

        result = history_service.get_filtered_history()

        mock_repo.find_with_filters.assert_called_once()

        assert result["filters"]["location"] is None

        assert result["filters"]["sensor_type"] is None

    def test_get_filtered_history_includes_filter_info(self, history_service, mock_repo):
        """Test que les filtres sont inclus dans la réponse"""

        mock_repo.find_with_filters.return_value = []

        result = history_service.get_filtered_history(
            location="cuisine", sensor_type="consommation", start_date="2026-01-01T00:00:00"
        )

        assert result["filters"]["location"] == "cuisine"

        assert result["filters"]["sensor_type"] == "consommation"

        assert result["filters"]["start_date"] == "2026-01-01T00:00:00"

    def test_get_filtered_history_with_limit(self, history_service, mock_repo):
        """Test avec limite de résultats"""

        mock_repo.find_with_filters.return_value = [{"id": i} for i in range(10)]

        result = history_service.get_filtered_history(limit=10)

        assert result["count"] == 10

        mock_repo.find_with_filters.assert_called_with(
            location=None, sensor_type=None, start_date=None, end_date=None, limit=10
        )
