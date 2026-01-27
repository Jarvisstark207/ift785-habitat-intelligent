from typing import List
from application.services.stats_service import StatsService
from application.services.alert_service import AlertService
from infrastructure.db.sqlite_sensor_repo import SQLiteSensorRepository


class DashboardService:
    """Service qui compose toutes les données du dashboard"""

    def __init__(
        self,
        repository: SQLiteSensorRepository,
        stats_service: StatsService,
        alert_service: AlertService
    ):
        self._repo = repository
        self._stats = stats_service
        self._alerts = alert_service

    def get_dashboard_data(self, locations: List[str]) -> dict:
        """Compose toutes les données du dashboard"""

        # Stats par location
        locations_data = {}
        for location in locations:
            locations_data[location] = self._stats.calculate_location_stats(
                location
            )

        # Stats globales
        global_stats = self._stats.calculate_global_stats(locations)

        # Alertes
        alerts = self._alerts.generate_alerts(locations)

        # Lectures récentes
        recent = self._repo.find_recent(20)

        # Historiques pour graphiques
        temp_history = self._repo.find_temperature_history(locations)
        consumption_current = self._repo.find_consumption_current(locations)

        return {
            "global": global_stats,
            "locations": locations_data,
            "alerts": alerts,
            "recent": recent,
            "temperature_history": temp_history,
            "consumption_current": consumption_current
        }
