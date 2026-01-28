from abc import ABC, abstractmethod
from domain.models.sensor_reading import SensorReading


class SensorSource(ABC):
    """Interface pour source de données capteurs (MQTT/simulation)"""

    @abstractmethod
    def get_next_reading(self) -> SensorReading:
        """Récupère la prochaine lecture (bloquant)"""
        pass

    @abstractmethod
    def is_simulation_mode(self) -> bool:
        """Indique si mode simulation"""
        pass
