"""Pattern Facade - Dashboard unifie de la maison intelligente"""

from typing import List

from domain.integrations.smart_home_adapter import SmartHomeAdapter


class DashboardFacade:
    """Facade fournissant une vue unifiee de la maison intelligente.

    Agregue les donnees provenant de multiples sous-systemes
    (capteurs, scenarios, profils, etat maison, integrations tierces)
    en un seul point d'acces simplifie.

    Sans la Facade, le client devrait connaitre et appeler directement
    chaque service interne. Ici, un seul appel suffit.
    """

    def __init__(
        self,
        repo=None,
        stats_service=None,
        alert_service=None,
        scenario_manager=None,
        profile_manager=None,
        house=None,
    ) -> None:
        self._repo = repo
        self._stats = stats_service
        self._alerts = alert_service
        self._scenarios = scenario_manager
        self._profiles = profile_manager
        self._house = house
        self._adapters: List[SmartHomeAdapter] = []

    def register_adapter(self, adapter: SmartHomeAdapter) -> None:
        """Enregistre une integration tierce dans le dashboard"""
        self._adapters.append(adapter)
