"""
Dependency Injection Container - Itération 6 (amélioré iter 8)
Enregistrement et résolution des dépendances.
Iter 8 : résolution automatique par introspection (inspect.signature + get_type_hints).
"""

import inspect
from typing import get_type_hints


class DIContainer:
    """
    Conteneur d'injection de dépendances.
    - Enregistrement par nom (str) : compatibilité legacy.
    - Enregistrement par type (type) : résolution automatique par introspection.
    """

    def __init__(self):
        self._factories = {}        # str -> factory (legacy)
        self._bindings = {}         # type -> type (introspection iter 8)
        self._singletons = {}       # clé -> instance singleton
        self._singleton_keys = set()

    def register(self, abstraction, implementation=None, singleton: bool = False):
        """
        Enregistre un service.
        - register("name", factory)         : enregistrement legacy par nom
        - register(AbstractType, ConcreteType) : enregistrement par type (introspection)
        """
        if isinstance(abstraction, str):
            self._factories[abstraction] = implementation
            if singleton:
                self._singleton_keys.add(abstraction)
        else:
            self._bindings[abstraction] = implementation
            if singleton:
                self._singleton_keys.add(abstraction)

    def resolve(self, service):
        """
        Résout et retourne le service demandé.
        - resolve("name")    : résolution legacy par nom
        - resolve(SomeType)  : résolution par type avec introspection automatique
        """
        if isinstance(service, str):
            return self._resolve_by_name(service)
        return self._resolve_type(service)

    def _resolve_by_name(self, name: str):
        """Résolution legacy par nom de service."""
        if name not in self._factories:
            raise KeyError(f"Service '{name}' non enregistré dans le container")
        if name in self._singleton_keys:
            if name not in self._singletons:
                self._singletons[name] = self._factories[name]()
            return self._singletons[name]
        return self._factories[name]()

    def _resolve_type(self, cls):
        """
        Résolution par type avec introspection automatique.
        Lit inspect.signature(cls.__init__) et get_type_hints() pour injecter
        récursivement chaque dépendance typée.
        """
        implementation = self._bindings.get(cls, cls)
        if implementation is None:
            raise ValueError(
                f"Dépendance '{cls.__name__}' non enregistrée dans le container"
            )
        kwargs = self._resolve_dependencies(implementation)
        return self._instantiate(implementation, kwargs)

    def _resolve_dependencies(self, implementation) -> dict:
        """Résout récursivement les dépendances typées d'une classe via introspection."""
        try:
            hints = get_type_hints(implementation.__init__)
        except Exception:
            hints = {}
        sig = inspect.signature(implementation.__init__)
        kwargs = {}
        for param_name, param in sig.parameters.items():
            if param_name == 'self' or param.default is not inspect.Parameter.empty:
                continue
            dep_type = hints.get(param_name)
            if dep_type is None:
                continue
            self._assert_registered(dep_type, implementation)
            kwargs[param_name] = self._resolve_type(dep_type)
        return kwargs

    def _assert_registered(self, dep_type, requester):
        """Lève ValueError si dep_type n'est pas enregistré."""
        if dep_type not in self._bindings and dep_type not in self._factories:
            raise ValueError(
                f"Dépendance '{dep_type.__name__}' requise par "
                f"'{requester.__name__}' n'est pas enregistrée dans le container"
            )

    def _instantiate(self, implementation, kwargs: dict):
        """Instancie la classe, en respectant le mode singleton si applicable."""
        if implementation in self._singleton_keys:
            if implementation not in self._singletons:
                self._singletons[implementation] = implementation(**kwargs)
            return self._singletons[implementation]
        return implementation(**kwargs)

    def is_registered(self, name) -> bool:
        """Vérifie si un service est enregistré (par nom ou par type)."""
        if isinstance(name, str):
            return name in self._factories
        return name in self._bindings

    def registered_services(self) -> list:
        """Retourne la liste des noms de services enregistrés (legacy)."""
        return list(self._factories.keys())


def build_default_container() -> DIContainer:
    """Construit le container DI par défaut avec les services de l'application."""
    from infrastructure.db.sqlalchemy_session import get_default_session_factory
    from infrastructure.db.unit_of_work import SQLAlchemyUnitOfWork
    from application.services.device_service import DeviceService

    container = DIContainer()

    session_factory = get_default_session_factory()
    container.register(
        "session_factory",
        lambda: session_factory,
        singleton=True
    )
    container.register(
        "unit_of_work",
        lambda: SQLAlchemyUnitOfWork(session_factory)
    )
    container.register(
        "device_service",
        lambda: DeviceService(),
        singleton=True
    )

    return container
