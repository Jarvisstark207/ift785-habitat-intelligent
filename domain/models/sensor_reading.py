from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict


@dataclass(frozen=True, slots=True)
class SensorReading:
    sensor_id: str
    location: str
    type: str
    value: Any
    unit: str
    timestamp: str

    @staticmethod
    def from_sensor_data(sensor_data: Any) -> "SensorReading":
        """
        Adapter minimal pour convertir ift785_client.SensorData -> SensorReading.
        On accepte Any pour éviter une dépendance directe au module MQTT dans le domain.
        """
        return SensorReading(
            sensor_id=sensor_data.sensor_id,
            location=sensor_data.location,
            type=sensor_data.type,
            value=sensor_data.value,
            unit=sensor_data.unit,
            timestamp=sensor_data.timestamp,
        )

    def to_db_tuple(self) -> tuple:
        """Ordre aligné avec la table sensor_readings de init_db.py."""
        return (self.sensor_id, self.location, self.type, self.value, self.unit, self.timestamp)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "sensor_id": self.sensor_id,
            "location": self.location,
            "type": self.type,
            "value": self.value,
            "unit": self.unit,
            "timestamp": self.timestamp,
        }
