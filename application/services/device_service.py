from __future__ import annotations

from typing import Any, Dict, List

from domain.models.device import Device
from domain.models.device_builder import DeviceBuilder
from domain.models.device_registry import DeviceRegistry


class DeviceService:
    """Service pour gérer les devices"""

    def __init__(self) -> None:
        """Initialise le service"""
        self.registry = DeviceRegistry.get_instance()
        self.builder = DeviceBuilder()

    def build_device(self, config: Dict[str, Any]) -> Device:
        """Construit un device à partir d'une configuration"""
        # Reset le builder pour une nouvelle construction
        self.builder.reset()

        # Configuration requise
        device_id = config.get("device_id")
        name = config.get("name")
        room_name = config.get("room_name")
        device_type = config.get("device_type")

        if not all([device_id, name, room_name, device_type]):
            raise ValueError(
                "device_id, name, room_name, and device_type are required"
            )

        # Configuration commune
        self.builder.set_device_id(device_id)
        self.builder.set_name(name)
        self.builder.set_room_name(room_name)
        self.builder.set_device_type(device_type)

        manufacturer = config.get("manufacturer", "generic")
        self.builder.set_manufacturer(manufacturer)

        # Configuration spécifique au type
        if device_type.lower() == "light":
            brightness = config.get("brightness", 100)
            color = config.get("color", "white")
            self.builder.set_brightness(brightness)
            self.builder.set_color(color)

        elif device_type.lower() == "thermostat":
            temperature = config.get("temperature", 20.0)
            target_temperature = config.get("target_temperature", 20.0)
            mode = config.get("mode", "auto")
            self.builder.set_temperature(temperature)
            self.builder.set_target_temperature(target_temperature)
            self.builder.set_mode(mode)

        elif device_type.lower() == "co2_sensor":
            ppm = config.get("ppm", 400.0)
            alarm_threshold = config.get("alarm_threshold", 1000.0)
            self.builder.set_ppm(ppm)
            self.builder.set_alarm_threshold(alarm_threshold)

        elif device_type.lower() == "motion_sensor":
            motion_detected = config.get("motion_detected", False)
            sensitivity = config.get("sensitivity", 5)
            self.builder.set_motion_detected(motion_detected)
            self.builder.set_sensitivity(sensitivity)

        # Construire et enregistrer le device
        device = self.builder.build()
        self.registry.register(device)
        return device

    def create_device(self, device: Device) -> None:
        """Crée et enregistre un device"""
        self.registry.register(device)

    def get_device(self, device_id: str) -> Device:
        """Récupère un device"""
        device = self.registry.get(device_id)
        if device is None:
            raise ValueError(f"Device {device_id} not found")
        return device

    def get_all_devices(self) -> List[Device]:
        """Récupère tous les devices"""
        return self.registry.get_all()

    def get_devices_by_type(self, device_type: str) -> List[Device]:
        """Récupère les devices d'un type"""
        return self.registry.get_by_type(device_type)

    def get_devices_by_room(self, room_name: str) -> List[Device]:
        """Récupère les devices d'une pièce"""
        return self.registry.get_by_room(room_name)

    def get_devices_by_manufacturer(self, manufacturer: str) -> List[Device]:
        """Récupère les devices d'un fabricant"""
        return self.registry.get_by_manufacturer(manufacturer)

    def delete_device(self, device_id: str) -> bool:
        """Supprime un device"""
        return self.registry.unregister(device_id)

    def device_exists(self, device_id: str) -> bool:
        """Vérifie si un device existe"""
        return self.registry.exists(device_id)

    def get_device_count(self) -> int:
        """Compte le nombre de devices"""
        return self.registry.count()
