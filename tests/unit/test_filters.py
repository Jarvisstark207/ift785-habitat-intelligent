"""Tests unitaires pour les systèmes de filtrage"""

from application.services.history_service import HistoryService
from application.services.stats_advanced_service import StatsAdvancedService


class TestHistoryFilters:
    """Tests pour le filtrage de l'historique"""

    def test_filter_by_location_only(self, mock_repo):
        mock_repo.find_with_filters.return_value = [
            {"sensor_id": "t1", "location": "salon", "value": 22.0}
        ]

        service = HistoryService(mock_repo)
        service.get_filtered_history(location="salon")

        mock_repo.find_with_filters.assert_called_once_with(
            location="salon", sensor_type=None, start_date=None, end_date=None, limit=100
        )

    def test_filter_by_sensor_type_only(self, mock_repo):
        mock_repo.find_with_filters.return_value = []

        service = HistoryService(mock_repo)
        service.get_filtered_history(sensor_type="temperature")

        call_args = mock_repo.find_with_filters.call_args[1]
        assert call_args["sensor_type"] == "temperature"
        assert call_args["location"] is None

    def test_filter_by_start_date_only(self, mock_repo):
        mock_repo.find_with_filters.return_value = []

        service = HistoryService(mock_repo)
        service.get_filtered_history(start_date="2026-01-01T00:00:00")

        call_args = mock_repo.find_with_filters.call_args[1]
        assert call_args["start_date"] == "2026-01-01T00:00:00"
        assert call_args["end_date"] is None

    def test_filter_by_end_date_only(self, mock_repo):
        mock_repo.find_with_filters.return_value = []

        service = HistoryService(mock_repo)
        service.get_filtered_history(end_date="2026-01-31T23:59:59")

        call_args = mock_repo.find_with_filters.call_args[1]
        assert call_args["end_date"] == "2026-01-31T23:59:59"
        assert call_args["start_date"] is None

    def test_filter_by_date_range(self, mock_repo):
        mock_repo.find_with_filters.return_value = []

        service = HistoryService(mock_repo)
        service.get_filtered_history(
            start_date="2026-01-01T00:00:00", end_date="2026-01-31T23:59:59"
        )

        call_args = mock_repo.find_with_filters.call_args[1]
        assert call_args["start_date"] == "2026-01-01T00:00:00"
        assert call_args["end_date"] == "2026-01-31T23:59:59"

    def test_filter_with_limit(self, mock_repo):
        mock_repo.find_with_filters.return_value = []

        service = HistoryService(mock_repo)
        service.get_filtered_history(limit=50)

        call_args = mock_repo.find_with_filters.call_args[1]
        assert call_args["limit"] == 50

    def test_filter_combined_location_and_type(self, mock_repo):
        mock_repo.find_with_filters.return_value = []

        service = HistoryService(mock_repo)
        service.get_filtered_history(location="salon", sensor_type="temperature")

        call_args = mock_repo.find_with_filters.call_args[1]
        assert call_args["location"] == "salon"
        assert call_args["sensor_type"] == "temperature"

    def test_filter_combined_all_params(self, mock_repo):
        mock_repo.find_with_filters.return_value = []

        service = HistoryService(mock_repo)
        service.get_filtered_history(
            location="salon",
            sensor_type="temperature",
            start_date="2026-01-01T00:00:00",
            end_date="2026-01-31T23:59:59",
            limit=50,
        )

        call_args = mock_repo.find_with_filters.call_args[1]
        assert call_args["location"] == "salon"
        assert call_args["sensor_type"] == "temperature"
        assert call_args["start_date"] == "2026-01-01T00:00:00"
        assert call_args["end_date"] == "2026-01-31T23:59:59"
        assert call_args["limit"] == 50

    def test_filter_returns_correct_count(self, mock_repo):
        mock_data = [{"id": i} for i in range(25)]
        mock_repo.find_with_filters.return_value = mock_data

        service = HistoryService(mock_repo)
        result = service.get_filtered_history()

        assert result["count"] == 25
        assert len(result["data"]) == 25

    def test_filter_includes_applied_filters_in_response(self, mock_repo):
        mock_repo.find_with_filters.return_value = []

        service = HistoryService(mock_repo)
        result = service.get_filtered_history(location="cuisine", sensor_type="consommation")

        assert result["filters"]["location"] == "cuisine"
        assert result["filters"]["sensor_type"] == "consommation"


class TestHourlyStatsFilters:
    """Tests pour le filtrage des stats horaires"""

    def test_hourly_filter_by_location(self, mock_repo):
        mock_repo.find_with_filters.return_value = []

        service = StatsAdvancedService(mock_repo)
        service.calculate_hourly_stats(location="salon", date="2026-02-03")

        call_args = mock_repo.find_with_filters.call_args[1]
        assert call_args["location"] == "salon"

    def test_hourly_filter_by_sensor_type(self, mock_repo):
        mock_repo.find_with_filters.return_value = []

        service = StatsAdvancedService(mock_repo)
        service.calculate_hourly_stats(sensor_type="consommation", date="2026-02-03")

        call_args = mock_repo.find_with_filters.call_args[1]
        assert call_args["sensor_type"] == "consommation"

    def test_hourly_filter_by_date(self, mock_repo):
        mock_repo.find_with_filters.return_value = []

        service = StatsAdvancedService(mock_repo)
        service.calculate_hourly_stats(date="2026-02-03")

        call_args = mock_repo.find_with_filters.call_args[1]
        assert "2026-02-03" in call_args["start_date"]
        assert "2026-02-03" in call_args["end_date"]

    def test_hourly_filter_combined(self, mock_repo):
        mock_repo.find_with_filters.return_value = []

        service = StatsAdvancedService(mock_repo)
        service.calculate_hourly_stats(
            location="salon", sensor_type="temperature", date="2026-02-03"
        )

        call_args = mock_repo.find_with_filters.call_args[1]
        assert call_args["location"] == "salon"
        assert call_args["sensor_type"] == "temperature"
        assert "2026-02-03" in call_args["start_date"]

    def test_filter_response_metadata(self, mock_repo):
        mock_repo.find_with_filters.return_value = []

        service = StatsAdvancedService(mock_repo)
        result = service.calculate_hourly_stats(
            location="cuisine", sensor_type="temperature", date="2026-02-03"
        )

        assert result["location"] == "cuisine"
        assert result["sensor_type"] == "temperature"
        assert result["date"] == "2026-02-03"
