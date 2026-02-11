from __future__ import annotations

from typing import Dict, List, Optional

from domain.models.device import Device


class DeviceRegistry:
    """Singleton pattern pour enregistrer et gérer les devices globalement"""

    _instance: Optional[DeviceRegistry] = None
    _devices: Dict[str, Device] = {}

    def __new__(cls) -> DeviceRegistry:
        """Implémente le pattern Singleton"""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def register(self, device: Device) -> None:
        """Enregistre un device"""
        self._devices[device.device_id] = device

    def unregister(self, device_id: str) -> bool:
        """Désenregistre un device"""
        if device_id in self._devices:
            del self._devices[device_id]
            return True
        return False

    def get(self, device_id: str) -> Optional[Device]:
        """Récupère un device par son ID"""
        return self._devices.get(device_id)

    def get_all(self) -> List[Device]:
        """Récupère tous les devices"""
        return list(self._devices.values())

    def get_by_type(self, device_type: str) -> List[Device]:
        """Récupère tous les devices d'un type donné"""
        return [
            device
            for device in self._devices.values()
            if device.device_type == device_type
        ]

    def get_by_room(self, room_name: str) -> List[Device]:
        """Récupère tous les devices d'une pièce"""
        return [
            device
            for device in self._devices.values()
            if device.room_name == room_name
        ]

    def get_by_manufacturer(self, manufacturer: str) -> List[Device]:
        """Récupère tous les devices d'un fabricant"""
        return [
            device
            for device in self._devices.values()
            if device.manufacturer == manufacturer
        ]

    def exists(self, device_id: str) -> bool:
        """Vérifie si un device existe"""
        return device_id in self._devices

    def count(self) -> int:
        """Compte le nombre de devices"""
        return len(self._devices)

    def clear(self) -> None:
        """Vide le registre"""
        self._devices.clear()

    @classmethod
    def get_instance(cls) -> DeviceRegistry:
        """Retourne l'instance du singleton"""
        if cls._instance is None:
            cls._instance = cls()
        # Permet d'obtenir l'instance du registre pour l'utiliser dans
        # toute l'application
        return cls._instance
