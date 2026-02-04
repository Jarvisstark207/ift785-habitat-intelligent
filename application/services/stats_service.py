from typing import List
from infrastructure.db.sqlite_sensor_repo import SQLiteSensorRepository


class StatsService:
    """Service de calcul de statistiques"""

    def __init__(self, repository: SQLiteSensorRepository):
        self._repo = repository

    def calculate_location_stats(self, location: str) -> dict:
        """Calcule stats pour une pièce"""
        return self._repo.get_stats_for_location(location)

    def calculate_global_stats(self, locations: List[str]) -> dict:
        """Calcule stats globales maison"""
        total_consumption = self._repo.get_total_consumption(locations)
        occupied_rooms = self._repo.get_occupied_rooms_count()
        avg_temp = self._repo.get_average_temperature(locations)

        return {
            "total_consumption": total_consumption,
            "occupied_rooms": occupied_rooms,
            "avg_temp": avg_temp,
        }
