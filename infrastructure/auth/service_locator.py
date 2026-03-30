"""Service Locator Pattern - Resolution de services par contexte utilisateur - Iteration 7"""

from typing import Any, Callable, Dict, Optional
from infrastructure.auth.user_repository import UserDeviceRepository


class ServiceLocator:
    """
    Service Locator Pattern.
    Maintient un registre de factories de services avec support
    de services scopes par utilisateur pour l'isolation applicative.
    """

    _instance: Optional["ServiceLocator"] = None

    def __init__(self):
        self._factories: Dict[str, Callable] = {}
        self._singletons: Dict[str, Any] = {}
        self._singleton_keys: set = set()
        self._user_services: Dict[str, Dict[str, Any]] = {}

    @classmethod
    def get_instance(cls) -> "ServiceLocator":
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    @classmethod
    def reset(cls) -> None:
        """Reinitialise le singleton (pour les tests)."""
        cls._instance = None

    def register(self, name: str, factory: Callable, singleton: bool = False) -> None:
        """Enregistre une factory de service."""
        self._factories[name] = factory
        if singleton:
            self._singleton_keys.add(name)

    def resolve(self, name: str) -> Any:
        """Resout un service global (singleton ou transient)."""
        if name not in self._factories:
            raise KeyError(f"Service '{name}' non enregistre dans le ServiceLocator")
        if name in self._singleton_keys:
            if name not in self._singletons:
                self._singletons[name] = self._factories[name]()
            return self._singletons[name]
        return self._factories[name]()

    def resolve_for_user(self, name: str, user_id: str) -> Any:
        """Resout un service scope a un utilisateur specifique."""
        if name not in self._factories:
            raise KeyError(f"Service '{name}' non enregistre dans le ServiceLocator")
        if user_id not in self._user_services:
            self._user_services[user_id] = {}
        if name not in self._user_services[user_id]:
            self._user_services[user_id][name] = self._factories[name](user_id)
        return self._user_services[user_id][name]

    def is_registered(self, name: str) -> bool:
        return name in self._factories

    def registered_services(self) -> list:
        return list(self._factories.keys())

    def clear_user_context(self, user_id: str) -> None:
        """Supprime le contexte de services d'un utilisateur."""
        self._user_services.pop(user_id, None)


def build_default_service_locator() -> ServiceLocator:
    """Construit le ServiceLocator par defaut avec les services de l'application."""
    from application.services.auth_service import AuthService

    locator = ServiceLocator()
    locator.register("auth_service", lambda: AuthService(), singleton=True)
    locator.register(
        "user_device_repository",
        lambda user_id: UserDeviceRepository(user_id),
    )
    return locator
