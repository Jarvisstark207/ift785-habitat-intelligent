"""
Dependency Injection Container - Iteration 6
Enregistrement et resolution des dependances
"""


class DIContainer:
    """
    Conteneur d'injection de dependances.
    Permet d'enregistrer des fabriques et de resoudre les services.
    """

    def __init__(self):
        self._factories = {}
        self._singletons = {}
        self._singleton_keys = set()

    def register(self, name: str, factory, singleton: bool = False):
        """Enregistre une fabrique de service"""
        self._factories[name] = factory
        if singleton:
            self._singleton_keys.add(name)

    def resolve(self, name: str):
        """Resout et retourne le service demande"""
        if name not in self._factories:
            raise KeyError(f"Service '{name}' non enregistre dans le container")
        if name in self._singleton_keys:
            if name not in self._singletons:
                self._singletons[name] = self._factories[name]()
            return self._singletons[name]
        return self._factories[name]()

    def is_registered(self, name: str) -> bool:
        """Verifie si un service est enregistre"""
        return name in self._factories

    def registered_services(self) -> list:
        """Retourne la liste des services enregistres"""
        return list(self._factories.keys())


def build_default_container() -> DIContainer:
    """Construit le container DI par defaut avec les services de l'application"""
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
