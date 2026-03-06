"""Pattern Decorator - Ajout de comportements aux adapters d'integration"""

from datetime import datetime
from typing import List

from domain.integrations.smart_home_adapter import SmartHomeAdapter


class SmartHomeDecorator(SmartHomeAdapter):
    """Decorateur de base - wraps un adapter existant.

    Permet d'ajouter des comportements (logging, validation, retry)
    de facon transparente sans modifier l'adapter original.
    """

    def __init__(self, adapter: SmartHomeAdapter) -> None:
        self._adapter = adapter

    def get_status(self) -> dict:
        return self._adapter.get_status()

    def get_devices(self) -> List[dict]:
        return self._adapter.get_devices()

    def control_device(self, device_id: str, command: dict) -> dict:
        return self._adapter.control_device(device_id, command)

    def get_adapter_name(self) -> str:
        return self._adapter.get_adapter_name()


class LoggingDecorator(SmartHomeDecorator):
    """Decorateur de journalisation.

    Enregistre toutes les interactions avec l'adapter
    pour audit et debugging.
    """

    def __init__(self, adapter: SmartHomeAdapter) -> None:
        super().__init__(adapter)
        self._log: List[dict] = []

    def _record(self, method: str, params: dict, result: dict) -> None:
        """Enregistre un appel dans le journal"""
        self._log.append({
            "timestamp": datetime.now().isoformat(),
            "adapter": self.get_adapter_name(),
            "method": method,
            "params": params,
            "success": result.get("success", True),
        })

    def get_status(self) -> dict:
        result = self._adapter.get_status()
        self._record("get_status", {}, result)
        return result

    def get_devices(self) -> List[dict]:
        result = self._adapter.get_devices()
        self._record("get_devices", {}, {"success": True, "count": len(result)})
        return result

    def control_device(self, device_id: str, command: dict) -> dict:
        result = self._adapter.control_device(device_id, command)
        self._record("control_device", {"device_id": device_id, "command": command}, result)
        return result

    def get_log(self) -> List[dict]:
        """Retourne le journal des appels"""
        return list(self._log)

    def get_log_count(self) -> int:
        """Retourne le nombre d'entrees dans le journal"""
        return len(self._log)

    def clear_log(self) -> None:
        """Vide le journal"""
        self._log.clear()


class ValidationDecorator(SmartHomeDecorator):
    """Decorateur de validation.

    Verifie que les reponses de l'adapter respectent
    le format attendu par l'interface SmartHomeAdapter.
    """

    REQUIRED_STATUS_KEYS = {"adapter", "connected", "total_devices"}
    REQUIRED_DEVICE_KEYS = {"id", "name", "type", "status"}

    def get_status(self) -> dict:
        result = self._adapter.get_status()
        missing = self.REQUIRED_STATUS_KEYS - result.keys()
        if missing:
            raise ValueError(
                f"Statut invalide pour {self.get_adapter_name()}: "
                f"champs manquants {missing}"
            )
        return result

    def get_devices(self) -> List[dict]:
        devices = self._adapter.get_devices()
        for device in devices:
            missing = self.REQUIRED_DEVICE_KEYS - device.keys()
            if missing:
                raise ValueError(
                    f"Appareil invalide dans {self.get_adapter_name()}: "
                    f"champs manquants {missing}"
                )
        return devices

    def control_device(self, device_id: str, command: dict) -> dict:
        if not device_id:
            raise ValueError("device_id ne peut pas etre vide")
        if not isinstance(command, dict):
            raise ValueError("command doit etre un dictionnaire")
        return self._adapter.control_device(device_id, command)
