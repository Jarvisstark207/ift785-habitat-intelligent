"""Repository per User Pattern - Isolation applicative des donnees - Iteration 7"""

from typing import Dict, List, Optional


class UserDeviceRepository:
    """
    Repository Pattern scope a un utilisateur.
    Isole les devices par proprietaire au niveau applicatif.
    Chaque utilisateur possede sa propre instance de repository.
    """

    def __init__(self, user_id: str):
        self.user_id = user_id
        self._devices: Dict[str, dict] = {}

    def add_device(self, device_id: str, device_data: dict) -> dict:
        """Ajoute un device dans le repository de cet utilisateur."""
        device_data = dict(device_data)
        device_data["owner_id"] = self.user_id
        self._devices[device_id] = device_data
        return device_data

    def get_device(self, device_id: str) -> Optional[dict]:
        """Retourne un device par son identifiant."""
        return self._devices.get(device_id)

    def get_all(self) -> List[dict]:
        """Retourne tous les devices de cet utilisateur."""
        return list(self._devices.values())

    def remove_device(self, device_id: str) -> bool:
        """Supprime un device du repository."""
        if device_id in self._devices:
            del self._devices[device_id]
            return True
        return False

    def count(self) -> int:
        """Retourne le nombre de devices de cet utilisateur."""
        return len(self._devices)

    def clear(self) -> None:
        """Vide le repository."""
        self._devices.clear()
