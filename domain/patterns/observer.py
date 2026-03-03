"""Pattern Observer - Publication/Abonnement aux evenements IoT"""

from abc import ABC, abstractmethod
from typing import List


class Observer(ABC):
    """Interface Observer - recoit les notifications d'evenements"""

    @abstractmethod
    def update(self, event_type: str, data: dict) -> None:
        """Recoit une notification d'evenement"""
        pass


class Observable(ABC):
    """Interface Observable - publie des evenements aux observers"""

    def __init__(self) -> None:
        self._observers: List[Observer] = []

    def subscribe(self, observer: Observer) -> None:
        """Abonne un observer aux evenements"""
        if observer not in self._observers:
            self._observers.append(observer)

    def unsubscribe(self, observer: Observer) -> None:
        """Desabonne un observer"""
        if observer in self._observers:
            self._observers.remove(observer)

    def notify(self, event_type: str, data: dict) -> None:
        """Notifie tous les observers inscrits"""
        for observer in self._observers:
            observer.update(event_type, data)

    def get_observer_count(self) -> int:
        """Retourne le nombre d'observers"""
        return len(self._observers)
