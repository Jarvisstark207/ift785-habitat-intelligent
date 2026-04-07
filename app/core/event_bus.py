"""
EventBus déclaratif - Itération 9 : AOP / Event-Driven
Singleton EventBus avec abonnement déclaratif via @on_event.
Supporte handlers sync et async.
"""

import asyncio
import functools
import inspect
import logging
import threading
from typing import Callable, Dict, List, Any

logger = logging.getLogger(__name__)


class EventBus:
    """
    Bus d'événements global (singleton thread-safe).
    Enregistrement : @on_event("device.updated") ou bus.subscribe("device.updated", fn)
    Publication    : EventBus.instance().publish("device.updated", payload)
    """

    _instance = None
    _lock = threading.Lock()

    def __init__(self):
        self._subscribers: Dict[str, List[Callable]] = {}
        self._history: List[dict] = []
        self._max_history = 200

    @classmethod
    def instance(cls) -> "EventBus":
        """Retourne l'instance singleton (crée si inexistante)."""
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = cls()
        return cls._instance

    @classmethod
    def reset(cls) -> None:
        """Réinitialise le singleton (utile pour les tests)."""
        with cls._lock:
            cls._instance = None

    # ------------------------------------------------------------------
    # Abonnement
    # ------------------------------------------------------------------

    def subscribe(self, event_name: str, handler: Callable) -> None:
        """Abonne *handler* à l'événement *event_name*."""
        if event_name not in self._subscribers:
            self._subscribers[event_name] = []
        if handler not in self._subscribers[event_name]:
            self._subscribers[event_name].append(handler)
            logger.debug("[EventBus] subscribed %s → %s", event_name, handler.__name__)

    def unsubscribe(self, event_name: str, handler: Callable) -> None:
        """Désabonne *handler* de l'événement *event_name*."""
        if event_name in self._subscribers:
            self._subscribers[event_name] = [
                h for h in self._subscribers[event_name] if h is not handler
            ]

    # ------------------------------------------------------------------
    # Publication
    # ------------------------------------------------------------------

    def publish(self, event_name: str, payload: Any = None) -> None:
        """
        Publie *event_name* et appelle tous les handlers abonnés.
        Les exceptions dans les handlers sont attrapées et journalisées.
        """
        import datetime
        entry = {
            "event": event_name,
            "payload": payload,
            "timestamp": datetime.datetime.utcnow().isoformat(),
        }
        self._history.append(entry)
        if len(self._history) > self._max_history:
            self._history.pop(0)

        handlers = self._subscribers.get(event_name, [])
        for handler in handlers:
            self._call_handler(handler, event_name, payload)
