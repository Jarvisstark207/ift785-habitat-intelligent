from typing import List
from application.services.stats_service import StatsService
from config import ALERT_TEMP_MIN, ALERT_TEMP_MAX, ALERT_CONSUMPTION_MAX


class AlertService:
    def __init__(self, stats_service: StatsService):
        self._stats = stats_service
        # Configuration dynamique (en mémoire pour l'instant)
        self._config = {
            "temp_min": ALERT_TEMP_MIN,
            "temp_max": ALERT_TEMP_MAX,
            "consumption_max": ALERT_CONSUMPTION_MAX
        }
    
    def get_config(self) -> dict:
        """Retourne la configuration actuelle"""
        return {
            "temperature": {
                "min": self._config["temp_min"],
                "max": self._config["temp_max"]
            },
            "consumption": {
                "max": self._config["consumption_max"]
            }
        }
    
    def update_config(self, temp_min: float = None, temp_max: float = None, 
                      consumption_max: float = None) -> dict:
        """Met à jour la configuration"""
        if temp_min is not None:
            self._config["temp_min"] = temp_min
        if temp_max is not None:
            self._config["temp_max"] = temp_max
        if consumption_max is not None:
            self._config["consumption_max"] = consumption_max
        
        return self.get_config()
    
    def generate_alerts(self, locations: List[str]) -> List[dict]:
        """Génère alertes avec config dynamique"""
        alerts = []
        
        for location in locations:
            stats = self._stats.calculate_location_stats(location)
            
            # Alerte température
            if stats.get('temp_avg'):
                if stats['temp_avg'] < self._config["temp_min"]:
                    alerts.append({
                        'type': 'temperature',
                        'severity': 'warning',
                        'location': location,
                        'message': f"Température basse: {stats['temp_avg']}°C"
                    })
                elif stats['temp_avg'] > self._config["temp_max"]:
                    alerts.append({
                        'type': 'temperature',
                        'severity': 'warning',
                        'location': location,
                        'message': f"Température élevée: {stats['temp_avg']}°C"
                    })
            
            # Alerte consommation
            if stats.get('consumption'):
                if stats['consumption'] > self._config["consumption_max"]:
                    alerts.append({
                        'type': 'consumption',
                        'severity': 'critical',
                        'location': location,
                        'message': f"Consommation excessive: {stats['consumption']}W"
                    })
        
        return alerts