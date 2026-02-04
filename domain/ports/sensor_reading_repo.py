from abc import ABC, abstractmethod
from typing import List, Optional
from domain.models.sensor_reading import SensorReading


class SensorReadingRepository(ABC):
    """Interface pour accéder aux lectures de capteurs (port)"""

    @abstractmethod
    def save(self, reading: SensorReading) -> None:
        """Sauvegarde une lecture"""
        pass

    @abstractmethod
    def find_recent(self, limit: int = 20) -> List[dict]:
        """Trouve les N dernières lectures"""
        pass

    @abstractmethod
    def find_by_location_and_type(
        self, location: str, sensor_type: str, limit: int = 10
    ) -> List[SensorReading]:
        """Trouve lectures par location et type"""
        pass

    @abstractmethod
    def find_temperature_history(self, locations: List[str]) -> dict:
        """Historique températures pour graphique"""
        pass

    @abstractmethod
    def find_consumption_current(self, locations: List[str]) -> dict:
        """Consommation actuelle par location"""
        pass
