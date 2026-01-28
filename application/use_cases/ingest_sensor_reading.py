from domain.models.sensor_reading import SensorReading
from domain.ports.sensor_reading_repo import SensorReadingRepository


class IngestSensorReading:
    """Use case: ingérer une lecture de capteur"""

    def __init__(self, repository: SensorReadingRepository):
        self._repo = repository

    def execute(self, reading: SensorReading) -> None:
        """Sauvegarde la lecture et affiche log"""
        self._repo.save(reading)
        print(f"Insere: {reading.location}/{reading.type} = {reading.value}")
