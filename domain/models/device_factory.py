from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Dict

from domain.models.device import CO2Sensor, Light, MotionSensor, Thermostat


class DeviceFactory(ABC):
    """Classe abstraite pour la création de devices (Factory Method)"""

    @abstractmethod
    def create_light(
        self,
        device_id: str,
        name: str,
        room_name: str,
        brightness: int = 100,
        color: str = "white",
    ) -> Light:
        """Crée une ampoule intelligente"""
        pass

    @abstractmethod
    def create_thermostat(
        self,
        device_id: str,
        name: str,
        room_name: str,
        temperature: float = 20.0,
        target_temperature: float = 20.0,
        mode: str = "auto",
    ) -> Thermostat:
        """Crée un thermostat"""
        pass

    @abstractmethod
    def create_co2_sensor(
        self,
        device_id: str,
        name: str,
        room_name: str,
        ppm: float = 400.0,
        alarm_threshold: float = 1000.0,
    ) -> CO2Sensor:
        """Crée un capteur CO2"""
        pass

    @abstractmethod
    def create_motion_sensor(
        self,
        device_id: str,
        name: str,
        room_name: str,
        motion_detected: bool = False,
        sensitivity: int = 5,
    ) -> MotionSensor:
        """Crée un capteur de mouvement"""
        pass


class PhilipsFactory(DeviceFactory):
    """Fabrique de devices Philips (Abstract Factory)"""

    MANUFACTURER = "Philips"

    def create_light(
        self,
        device_id: str,
        name: str,
        room_name: str,
        brightness: int = 100,
        color: str = "white",
    ) -> Light:
        """Crée une ampoule Philips Hue"""
        return Light(
            device_id=device_id,
            name=name,
            room_name=room_name,
            device_type="light",
            manufacturer=self.MANUFACTURER,
            brightness=brightness,
            color=color,
        )

    def create_thermostat(
        self,
        device_id: str,
        name: str,
        room_name: str,
        temperature: float = 20.0,
        target_temperature: float = 20.0,
        mode: str = "auto",
    ) -> Thermostat:
        """Crée un thermostat Philips"""
        return Thermostat(
            device_id=device_id,
            name=name,
            room_name=room_name,
            device_type="thermostat",
            manufacturer=self.MANUFACTURER,
            temperature=temperature,
            target_temperature=target_temperature,
            mode=mode,
        )

    def create_co2_sensor(
        self,
        device_id: str,
        name: str,
        room_name: str,
        ppm: float = 400.0,
        alarm_threshold: float = 1000.0,
    ) -> CO2Sensor:
        """Crée un capteur CO2 Philips"""
        return CO2Sensor(
            device_id=device_id,
            name=name,
            room_name=room_name,
            device_type="co2_sensor",
            manufacturer=self.MANUFACTURER,
            ppm=ppm,
            alarm_threshold=alarm_threshold,
        )

    def create_motion_sensor(
        self,
        device_id: str,
        name: str,
        room_name: str,
        motion_detected: bool = False,
        sensitivity: int = 5,
    ) -> MotionSensor:
        """Crée un capteur de mouvement Philips"""
        return MotionSensor(
            device_id=device_id,
            name=name,
            room_name=room_name,
            device_type="motion_sensor",
            manufacturer=self.MANUFACTURER,
            motion_detected=motion_detected,
            sensitivity=sensitivity,
        )


class NestFactory(DeviceFactory):
    """Fabrique de devices Google Nest (Abstract Factory)"""

    MANUFACTURER = "Google Nest"

    def create_light(
        self,
        device_id: str,
        name: str,
        room_name: str,
        brightness: int = 100,
        color: str = "white",
    ) -> Light:
        """Crée une ampoule Nest"""
        return Light(
            device_id=device_id,
            name=name,
            room_name=room_name,
            device_type="light",
            manufacturer=self.MANUFACTURER,
            brightness=brightness,
            color=color,
        )

    def create_thermostat(
        self,
        device_id: str,
        name: str,
        room_name: str,
        temperature: float = 20.0,
        target_temperature: float = 20.0,
        mode: str = "auto",
    ) -> Thermostat:
        """Crée un thermostat Google Nest"""
        return Thermostat(
            device_id=device_id,
            name=name,
            room_name=room_name,
            device_type="thermostat",
            manufacturer=self.MANUFACTURER,
            temperature=temperature,
            target_temperature=target_temperature,
            mode=mode,
        )

    def create_co2_sensor(
        self,
        device_id: str,
        name: str,
        room_name: str,
        ppm: float = 400.0,
        alarm_threshold: float = 1000.0,
    ) -> CO2Sensor:
        """Crée un capteur CO2 Nest"""
        return CO2Sensor(
            device_id=device_id,
            name=name,
            room_name=room_name,
            device_type="co2_sensor",
            manufacturer=self.MANUFACTURER,
            ppm=ppm,
            alarm_threshold=alarm_threshold,
        )

    def create_motion_sensor(
        self,
        device_id: str,
        name: str,
        room_name: str,
        motion_detected: bool = False,
        sensitivity: int = 5,
    ) -> MotionSensor:
        """Crée un capteur de mouvement Nest"""
        return MotionSensor(
            device_id=device_id,
            name=name,
            room_name=room_name,
            device_type="motion_sensor",
            manufacturer=self.MANUFACTURER,
            motion_detected=motion_detected,
            sensitivity=sensitivity,
        )


class GenericFactory(DeviceFactory):
    """Fabrique de devices génériques (Abstract Factory)"""

    MANUFACTURER = "Generic"

    def create_light(
        self,
        device_id: str,
        name: str,
        room_name: str,
        brightness: int = 100,
        color: str = "white",
    ) -> Light:
        """Crée une ampoule générique"""
        return Light(
            device_id=device_id,
            name=name,
            room_name=room_name,
            device_type="light",
            manufacturer=self.MANUFACTURER,
            brightness=brightness,
            color=color,
        )

    def create_thermostat(
        self,
        device_id: str,
        name: str,
        room_name: str,
        temperature: float = 20.0,
        target_temperature: float = 20.0,
        mode: str = "auto",
    ) -> Thermostat:
        """Crée un thermostat générique"""
        return Thermostat(
            device_id=device_id,
            name=name,
            room_name=room_name,
            device_type="thermostat",
            manufacturer=self.MANUFACTURER,
            temperature=temperature,
            target_temperature=target_temperature,
            mode=mode,
        )

    def create_co2_sensor(
        self,
        device_id: str,
        name: str,
        room_name: str,
        ppm: float = 400.0,
        alarm_threshold: float = 1000.0,
    ) -> CO2Sensor:
        """Crée un capteur CO2 générique"""
        return CO2Sensor(
            device_id=device_id,
            name=name,
            room_name=room_name,
            device_type="co2_sensor",
            manufacturer=self.MANUFACTURER,
            ppm=ppm,
            alarm_threshold=alarm_threshold,
        )

    def create_motion_sensor(
        self,
        device_id: str,
        name: str,
        room_name: str,
        motion_detected: bool = False,
        sensitivity: int = 5,
    ) -> MotionSensor:
        """Crée un capteur de mouvement générique"""
        return MotionSensor(
            device_id=device_id,
            name=name,
            room_name=room_name,
            device_type="motion_sensor",
            manufacturer=self.MANUFACTURER,
            motion_detected=motion_detected,
            sensitivity=sensitivity,
        )


class DeviceFactoryProvider:
    """Provider pour obtenir la bonne fabrique selon le fabricant"""

    _factories: Dict[str, DeviceFactory] = {
        "philips": PhilipsFactory(),
        "nest": NestFactory(),
        "generic": GenericFactory(),
    }

    @classmethod
    def get_factory(cls, manufacturer: str) -> DeviceFactory:
        """Retourne la fabrique appropriée"""
        factory = cls._factories.get(manufacturer.lower())
        if factory is None:
            return cls._factories["generic"]
        return factory

    @classmethod
    def register_factory(cls, name: str, factory: DeviceFactory) -> None:
        """Enregistre une nouvelle fabrique"""
        cls._factories[name.lower()] = factory
