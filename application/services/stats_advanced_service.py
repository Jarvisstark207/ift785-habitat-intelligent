"""Service de statistiques avancées"""

from typing import Optional
from datetime import datetime
from infrastructure.db.sqlite_sensor_repo import SQLiteSensorRepository


class StatsAdvancedService:
    """Calculs statistiques avancés par heure"""

    def __init__(self, repository: SQLiteSensorRepository):
        self._repo = repository

    def calculate_hourly_stats(
        self,
        location: Optional[str] = None,
        sensor_type: str = "temperature",
        date: Optional[str] = None,
    ) -> dict:
        """Calcule statistiques par heure pour une journée"""

        # Si pas de date, prendre aujourd'hui
        if not date:
            date = datetime.now().strftime("%Y-%m-%d")

        # Calculer début et fin de journée
        start_date = f"{date}T00:00:00"
        end_date = f"{date}T23:59:59"

        # Récupérer toutes les lectures de la journée
        readings = self._repo.find_with_filters(
            location=location,
            sensor_type=sensor_type,
            start_date=start_date,
            end_date=end_date,
            limit=1000,
        )

        # Grouper par heure
        hourly_data = {}
        for reading in readings:
            timestamp = reading["timestamp"]
            hour = timestamp[:13]  # Format: "2026-02-01T14"

            if hour not in hourly_data:
                hourly_data[hour] = []

            hourly_data[hour].append(reading["value"])

        # Calculer statistiques pour chaque heure
        result = []
        for hour in sorted(hourly_data.keys()):
            values = hourly_data[hour]
            result.append(
                {
                    "hour": hour,
                    "avg": round(sum(values) / len(values), 2),
                    "min": round(min(values), 2),
                    "max": round(max(values), 2),
                    "count": len(values),
                }
            )

        return {
            "date": date,
            "location": location,
            "sensor_type": sensor_type,
            "hourly_stats": result,
        }
