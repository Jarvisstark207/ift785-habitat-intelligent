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
