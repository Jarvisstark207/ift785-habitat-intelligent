"""Pattern Mediator - Coordination centralisee entre dispositifs IoT"""

from abc import ABC, abstractmethod
from typing import Callable, Dict, List


class Mediator(ABC):
    """Interface Mediator - centralise la communication entre composants"""

    @abstractmethod
    def notify(self, sender: str, event: str, data: dict) -> None:
        """Traite un evenement envoye par un composant"""
        pass


class DeviceMediator(Mediator):
    """Mediateur de dispositifs IoT.

    Coordonne les reactions entre dispositifs sans couplage direct.
    Exemple : thermostat + ventilateur + fenetre repondent ensemble
    a un evenement temperature sans se connaitre mutuellement.
    """

    def __init__(self) -> None:
        self._handlers: Dict[str, List[Callable]] = {}
        self._event_log: List[dict] = []

    def register(self, event_type: str, handler: Callable) -> None:
        """Enregistre un gestionnaire pour un type d'evenement"""
        if event_type not in self._handlers:
            self._handlers[event_type] = []
        self._handlers[event_type].append(handler)

    def unregister(self, event_type: str, handler: Callable) -> None:
        """Supprime un gestionnaire"""
        if event_type in self._handlers:
            self._handlers[event_type] = [
                h for h in self._handlers[event_type] if h != handler
            ]

    def notify(self, sender: str, event: str, data: dict) -> None:
        """Notifie tous les gestionnaires enregistres pour l'evenement"""
        self._event_log.append({"sender": sender, "event": event, "data": data})
        for handler in self._handlers.get(event, []):
            handler(sender, data)

    def get_handler_count(self, event_type: str) -> int:
        """Retourne le nombre de gestionnaires pour un evenement"""
        return len(self._handlers.get(event_type, []))

    def get_event_log(self) -> List[dict]:
        """Retourne le journal des evenements traites"""
        return self._event_log
