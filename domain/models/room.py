from __future__ import annotations
from dataclasses import dataclass, field
from typing import List

from domain.models.device import Device


@dataclass
class Room:
    """Représente une pièce de l'habitat"""

    name: str
    devices: List[Device] = field(default_factory=list)

    def add_device(self, device: "Device") -> None:
        """Ajoute un appareil à la pièce"""
        self.devices.append(device)

    def get_device_count(self) -> int:
        """Retourne le nombre d'appareils"""
        return len(self.devices)
