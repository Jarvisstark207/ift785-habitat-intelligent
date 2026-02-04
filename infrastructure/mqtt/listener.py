import time
from domain.ports.sensor_source import SensorSource
from application.use_cases.ingest_sensor_reading import IngestSensorReading


class SensorListener:
    """Service qui écoute les capteurs et ingère les données"""

    def __init__(self, sensor_source: SensorSource, ingest_use_case: IngestSensorReading):
        self._source = sensor_source
        self._ingest = ingest_use_case

    def start_listening(self) -> None:
        """Démarre boucle d'écoute (bloquant)"""
        print("Demarrage thread collecte donnees...")

        if self._source.is_simulation_mode():
            print("Mode SIMULATION active")
        else:
            print("Mode MQTT REEL actif")

        while True:
            try:
                reading = self._source.get_next_reading()
                self._ingest.execute(reading)
            except Exception as e:
                print(f"Erreur collecte: {e}")
                time.sleep(1)
