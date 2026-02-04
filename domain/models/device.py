from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Optional
from domain.models.sensor import Sensor


@dataclass
class Device:
    """Représente un appareil IoT avec ses capteurs"""

    device_id: str
    room_name: str
    sensors: List[Sensor] = field(default_factory=list)

    def add_sensor(self, sensor: Sensor) -> None:
        """Ajoute un capteur à l'appareil"""
        self.sensors.append(sensor)

    def get_sensor_by_type(self, sensor_type: str) -> Optional[Sensor]:
        """Trouve un capteur par son type"""
        for sensor in self.sensors:
            if sensor.matches_type(sensor_type):
                return sensor
        return None

    def get_all_sensor_types(self) -> List[str]:
        """Retourne tous les types de capteurs"""
        return [sensor.type for sensor in self.sensors]
