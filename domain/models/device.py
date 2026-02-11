from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional
from domain.models.sensor import Sensor


@dataclass
class Device(ABC):
    """Classe abstraite représentant un appareil IoT"""

    device_id: str
    name: str
    room_name: str
    device_type: str
    manufacturer: str = "Generic"
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

    @abstractmethod
    def get_status(self) -> Dict[str, Any]:
        """Retourne le statut de l'appareil"""
        pass

    @abstractmethod
    def to_dict(self) -> Dict[str, Any]:
        """Convertit l'appareil en dictionnaire"""
        pass


@dataclass
class Light(Device):
    """Représente une ampoule intelligente (ex: Philips Hue)"""

    brightness: int = 100
    color: str = "white"

    def __post_init__(self) -> None:
        if not hasattr(self, "device_type"):
            self.device_type = "light"

    def get_status(self) -> Dict[str, Any]:
        """Retourne le statut de l'ampoule"""
        return {
            "device_id": self.device_id,
            "name": self.name,
            "type": self.device_type,
            "brightness": self.brightness,
            "color": self.color,
            "room": self.room_name,
            "manufacturer": self.manufacturer,
        }

    def to_dict(self) -> Dict[str, Any]:
        """Convertit l'ampoule en dictionnaire"""
        return {
            "device_id": self.device_id,
            "name": self.name,
            "type": self.device_type,
            "brightness": self.brightness,
            "color": self.color,
            "room": self.room_name,
            "manufacturer": self.manufacturer,
            "sensors": [sensor.to_dict() for sensor in self.sensors],
        }


@dataclass
class Thermostat(Device):
    """Représente un thermostat intelligent (ex: Nest)"""

    temperature: float = 20.0
    target_temperature: float = 20.0
    mode: str = "auto"  # heat, cool, auto

    def __post_init__(self) -> None:
        if not hasattr(self, "device_type"):
            self.device_type = "thermostat"

    def get_status(self) -> Dict[str, Any]:
        """Retourne le statut du thermostat"""
        return {
            "device_id": self.device_id,
            "name": self.name,
            "type": self.device_type,
            "temperature": self.temperature,
            "target_temperature": self.target_temperature,
            "mode": self.mode,
            "room": self.room_name,
            "manufacturer": self.manufacturer,
        }

    def to_dict(self) -> Dict[str, Any]:
        """Convertit le thermostat en dictionnaire"""
        return {
            "device_id": self.device_id,
            "name": self.name,
            "type": self.device_type,
            "temperature": self.temperature,
            "target_temperature": self.target_temperature,
            "mode": self.mode,
            "room": self.room_name,
            "manufacturer": self.manufacturer,
            "sensors": [sensor.to_dict() for sensor in self.sensors],
        }


@dataclass
class CO2Sensor(Device):
    """Représente un capteur de CO2"""

    ppm: float = 400.0
    alarm_threshold: float = 1000.0

    def __post_init__(self) -> None:
        if not hasattr(self, "device_type"):
            self.device_type = "co2_sensor"

    def get_status(self) -> Dict[str, Any]:
        """Retourne le statut du capteur"""
        return {
            "device_id": self.device_id,
            "name": self.name,
            "type": self.device_type,
            "ppm": self.ppm,
            "alarm_threshold": self.alarm_threshold,
            "alarm_active": self.ppm > self.alarm_threshold,
            "room": self.room_name,
            "manufacturer": self.manufacturer,
        }

    def to_dict(self) -> Dict[str, Any]:
        """Convertit le capteur en dictionnaire"""
        return {
            "device_id": self.device_id,
            "name": self.name,
            "type": self.device_type,
            "ppm": self.ppm,
            "alarm_threshold": self.alarm_threshold,
            "alarm_active": self.ppm > self.alarm_threshold,
            "room": self.room_name,
            "manufacturer": self.manufacturer,
            "sensors": [sensor.to_dict() for sensor in self.sensors],
        }


@dataclass
class MotionSensor(Device):
    """Représente un capteur de mouvement"""

    motion_detected: bool = False
    sensitivity: int = 5  # 1-10

    def __post_init__(self) -> None:
        if not hasattr(self, "device_type"):
            self.device_type = "motion_sensor"

    def get_status(self) -> Dict[str, Any]:
        """Retourne le statut du capteur"""
        return {
            "device_id": self.device_id,
            "name": self.name,
            "type": self.device_type,
            "motion_detected": self.motion_detected,
            "sensitivity": self.sensitivity,
            "room": self.room_name,
            "manufacturer": self.manufacturer,
        }

    def to_dict(self) -> Dict[str, Any]:
        """Convertit le capteur en dictionnaire"""
        return {
            "device_id": self.device_id,
            "name": self.name,
            "type": self.device_type,
            "motion_detected": self.motion_detected,
            "sensitivity": self.sensitivity,
            "room": self.room_name,
            "manufacturer": self.manufacturer,
            "sensors": [sensor.to_dict() for sensor in self.sensors],
        }
