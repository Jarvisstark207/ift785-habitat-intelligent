"""Service pour gérer l'historique des données"""

from typing import Optional, List
from infrastructure.db.sqlite_sensor_repo import SQLiteSensorRepository


class HistoryService:
    """Service de gestion de l'historique"""

    def __init__(self, repository: SQLiteSensorRepository):
        self._repo = repository

    def get_filtered_history(
        self,
        location: Optional[str] = None,
        sensor_type: Optional[str] = None,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        limit: int = 100,
    ) -> dict:
        """Récupère historique avec filtres"""
        readings = self._repo.find_with_filters(
            location=location,
            sensor_type=sensor_type,
            start_date=start_date,
            end_date=end_date,
            limit=limit,
        )

        return {
            "count": len(readings),
            "filters": {
                "location": location,
                "sensor_type": sensor_type,
                "start_date": start_date,
                "end_date": end_date,
            },
            "data": readings,
        }
