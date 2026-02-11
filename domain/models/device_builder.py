from __future__ import annotations

from typing import Optional

from domain.models.device import Device
from domain.models.device_factory import DeviceFactoryProvider


class DeviceBuilder:
    """Builder pattern pour la construction progressive de devices"""

    def __init__(self) -> None:
        """Initialise le builder"""
        self._device_id: Optional[str] = None
        self._name: Optional[str] = None
        self._room_name: Optional[str] = None
        self._device_type: Optional[str] = None
        self._manufacturer: str = "generic"
        self._brightness: int = 100
        self._color: str = "white"
        self._temperature: float = 20.0
        self._target_temperature: float = 20.0
        self._mode: str = "auto"
        self._ppm: float = 400.0
        self._alarm_threshold: float = 1000.0
        self._motion_detected: bool = False
        self._sensitivity: int = 5

    def set_device_id(self, device_id: str) -> DeviceBuilder:
        """Définit l'ID du device"""
        self._device_id = device_id
        return self

    def set_name(self, name: str) -> DeviceBuilder:
        """Définit le nom du device"""
        self._name = name
        return self

    def set_room_name(self, room_name: str) -> DeviceBuilder:
        """Définit la pièce du device"""
        self._room_name = room_name
        return self

    def set_device_type(self, device_type: str) -> DeviceBuilder:
        """Définit le type de device"""
        self._device_type = device_type
        return self

    def set_manufacturer(self, manufacturer: str) -> DeviceBuilder:
        """Définit le fabricant"""
        self._manufacturer = manufacturer
        return self

    # Light-specific methods
    def set_brightness(self, brightness: int) -> DeviceBuilder:
        """Définit la luminosité"""
        if 0 <= brightness <= 100:
            self._brightness = brightness
        return self

    def set_color(self, color: str) -> DeviceBuilder:
        """Définit la couleur"""
        self._color = color
        return self

    # Thermostat-specific methods
    def set_temperature(self, temperature: float) -> DeviceBuilder:
        """Définit la température actuelle"""
        self._temperature = temperature
        return self

    def set_target_temperature(self, target_temperature: float) -> DeviceBuilder:
        """Définit la température cible"""
        self._target_temperature = target_temperature
        return self

    def set_mode(self, mode: str) -> DeviceBuilder:
        """Définit le mode (heat, cool, auto)"""
        if mode in ["heat", "cool", "auto"]:
            self._mode = mode
        return self

    # CO2Sensor-specific methods
    def set_ppm(self, ppm: float) -> DeviceBuilder:
        """Définit le niveau de CO2 en ppm"""
        self._ppm = ppm
        return self

    def set_alarm_threshold(self, alarm_threshold: float) -> DeviceBuilder:
        """Définit le seuil d'alarme"""
        self._alarm_threshold = alarm_threshold
        return self

    # MotionSensor-specific methods
    def set_motion_detected(self, motion_detected: bool) -> DeviceBuilder:
        """Définit si du mouvement est détecté"""
        self._motion_detected = motion_detected
        return self

    def set_sensitivity(self, sensitivity: int) -> DeviceBuilder:
        """Définit la sensibilité (1-10)"""
        if 1 <= sensitivity <= 10:
            self._sensitivity = sensitivity
        return self

    def build(self) -> Device:
        """Construit le device"""
        if not self._device_id:
            raise ValueError("device_id is required")
        if not self._name:
            raise ValueError("name is required")
        if not self._room_name:
            raise ValueError("room_name is required")
        if not self._device_type:
            raise ValueError("device_type is required")

        factory = DeviceFactoryProvider.get_factory(self._manufacturer)

        if self._device_type.lower() == "light":
            return factory.create_light(
                device_id=self._device_id,
                name=self._name,
                room_name=self._room_name,
                brightness=self._brightness,
                color=self._color,
            )
        elif self._device_type.lower() == "thermostat":
            return factory.create_thermostat(
                device_id=self._device_id,
                name=self._name,
                room_name=self._room_name,
                temperature=self._temperature,
                target_temperature=self._target_temperature,
                mode=self._mode,
            )
        elif self._device_type.lower() == "co2_sensor":
            return factory.create_co2_sensor(
                device_id=self._device_id,
                name=self._name,
                room_name=self._room_name,
                ppm=self._ppm,
                alarm_threshold=self._alarm_threshold,
            )
        elif self._device_type.lower() == "motion_sensor":
            return factory.create_motion_sensor(
                device_id=self._device_id,
                name=self._name,
                room_name=self._room_name,
                motion_detected=self._motion_detected,
                sensitivity=self._sensitivity,
            )
        else:
            raise ValueError(
                f"Unknown device_type: {self._device_type}"
            )

    def reset(self) -> DeviceBuilder:
        """Réinitialise le builder"""
        self._device_id = None
        self._name = None
        self._room_name = None
        self._device_type = None
        self._manufacturer = "generic"
        self._brightness = 100
        self._color = "white"
        self._temperature = 20.0
        self._target_temperature = 20.0
        self._mode = "auto"
        self._ppm = 400.0
        self._alarm_threshold = 1000.0
        self._motion_detected = False
        self._sensitivity = 5
        return self
