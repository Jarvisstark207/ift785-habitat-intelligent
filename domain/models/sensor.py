from dataclasses import dataclass
from typing import Optional


@dataclass
class Sensor:
    """Représente un capteur physique"""
    sensor_id: str
    type: str
    unit: str
    location: Optional[str] = None

    def matches_type(self, sensor_type: str) -> bool:
        """Vérifie si le capteur est du type spécifié"""
        return self.type == sensor_type