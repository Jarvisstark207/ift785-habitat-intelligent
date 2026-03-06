"""Pattern Adapter - Adaptation d'APIs tierces vers une interface commune"""

from abc import ABC, abstractmethod
from typing import List


class SmartHomeAdapter(ABC):
    """Interface commune pour toutes les integrations domotiques.

    Permet d'utiliser des APIs tierces (Philips Hue, Nest, etc.)
    de facon uniforme sans connaitre leurs details d'implementation.
    """

    @abstractmethod
    def get_status(self) -> dict:
        """Retourne le statut general du systeme"""
        pass

    @abstractmethod
    def get_devices(self) -> List[dict]:
        """Retourne la liste des appareils disponibles"""
        pass

    @abstractmethod
    def control_device(self, device_id: str, command: dict) -> dict:
        """Envoie une commande a un appareil"""
        pass

    @abstractmethod
    def get_adapter_name(self) -> str:
        """Retourne le nom de l'integration"""
        pass