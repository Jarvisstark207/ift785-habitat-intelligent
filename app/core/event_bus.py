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

    def _call_handler(self, handler: Callable, event_name: str, payload: Any) -> None:
        """Appelle un handler, sync ou async, en avalant les exceptions."""
        try:
            if inspect.iscoroutinefunction(handler):
                try:
                    loop = asyncio.get_event_loop()
                    if loop.is_running():
                        loop.create_task(handler(event_name, payload))
                    else:
                        loop.run_until_complete(handler(event_name, payload))
                except RuntimeError:
                    asyncio.run(handler(event_name, payload))
            else:
                handler(event_name, payload)
        except Exception as exc:
            logger.error(
                "[EventBus] handler %s raised %s: %s",
                handler.__name__, type(exc).__name__, exc
            )

    # ------------------------------------------------------------------
    # Introspection
    # ------------------------------------------------------------------

    def subscribers(self, event_name: str) -> List[Callable]:
        """Retourne la liste des handlers abonnés à *event_name*."""
        return list(self._subscribers.get(event_name, []))

    def all_subscribers(self) -> Dict[str, List[str]]:
        """Retourne {event_name: [handler_name, ...]} pour tous les événements."""
        return {k: [h.__name__ for h in v] for k, v in self._subscribers.items()}

    def get_history(self) -> List[dict]:
        """Retourne l'historique des événements publiés (les N derniers)."""
        return list(self._history)

    def clear_history(self) -> None:
        """Vide l'historique des événements."""
        self._history.clear()


# ---------------------------------------------------------------------------
# Décorateur @on_event
# ---------------------------------------------------------------------------

def on_event(event_name: str):
    """
    Décorateur déclaratif pour abonner une fonction à un événement du bus.

    Usage ::

        @on_event("device.updated")
        def handle_device_update(event, payload):
            print(f"Device updated: {payload}")
    """
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            return func(*args, **kwargs)

        wrapper._on_event = event_name
        EventBus.instance().subscribe(event_name, wrapper)
        return wrapper
    return decorator
