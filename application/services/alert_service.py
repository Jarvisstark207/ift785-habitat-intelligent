from typing import List
from application.services.stats_service import StatsService
from config import ALERT_TEMP_MIN, ALERT_TEMP_MAX, ALERT_CONSUMPTION_MAX


class AlertService:
    """Service de génération d'alertes"""

    def __init__(self, stats_service: StatsService):
        self._stats = stats_service

    def generate_alerts(self, locations: List[str]) -> List[str]:
        """Génère les alertes pour toutes les locations"""
        alerts = []

        # Alertes par pièce
        for location in locations:
            stats = self._stats.calculate_location_stats(location)

            if stats['temp_avg']:
                if stats['temp_avg'] < ALERT_TEMP_MIN:
                    msg = f"{location}: Temperature basse ({stats['temp_avg']}C)"
                    alerts.append(msg)
                elif stats['temp_avg'] > ALERT_TEMP_MAX:
                    msg = f"{location}: Temperature elevee ({stats['temp_avg']}C)"
                    alerts.append(msg)

        # Alertes globales
        global_stats = self._stats.calculate_global_stats(locations)
        if global_stats['total_consumption'] > ALERT_CONSUMPTION_MAX:
            msg = f"Consommation elevee: {global_stats['total_consumption']}W"
            alerts.append(msg)

        return alerts
