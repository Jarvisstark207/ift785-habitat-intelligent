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

