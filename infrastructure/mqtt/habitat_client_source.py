from domain.ports.sensor_source import SensorSource
from domain.models.sensor_reading import SensorReading
from ift785_client import HabitatClient


class HabitatClientSource(SensorSource):
    """Adapte HabitatClient vers interface SensorSource"""

    def __init__(self):
        self._client = HabitatClient()

    def get_next_reading(self) -> SensorReading:
        """Récupère prochaine lecture depuis MQTT/simulation"""
        sensor_data = self._client.get_next_sensor_data()
        return SensorReading.from_sensor_data(sensor_data)

    def is_simulation_mode(self) -> bool:
        """Indique si en mode simulation"""
        return self._client.is_simulation_mode()
