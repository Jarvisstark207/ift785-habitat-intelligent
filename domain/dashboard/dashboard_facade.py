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

    def get_summary(self) -> dict:
        """Retourne un resume global de la maison en un seul appel.

        Agregue: mode maison, profil actif, alertes, scenarios,
        et le statut des integrations tierces.
        """
        summary = {
            "house_mode": self._get_house_mode(),
            "active_profile": self._get_active_profile(),
            "alerts": self._get_alerts_summary(),
            "scenarios": self._get_scenarios_summary(),
            "integrations": self._get_integrations_summary(),
        }
        return summary
