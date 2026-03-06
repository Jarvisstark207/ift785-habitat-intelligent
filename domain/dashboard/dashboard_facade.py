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

    def get_widgets(self) -> List[dict]:
        """Retourne les donnees formatees pour les widgets du dashboard."""
        widgets = [
            {
                "id": "house_mode",
                "title": "Mode Maison",
                "type": "status",
                "data": {"mode": self._get_house_mode()},
            },
            {
                "id": "alerts",
                "title": "Alertes Actives",
                "type": "counter",
                "data": self._get_alerts_summary(),
            },
            {
                "id": "scenarios",
                "title": "Scenarios",
                "type": "list",
                "data": self._get_scenarios_summary(),
            },
            {
                "id": "integrations",
                "title": "Integrations",
                "type": "grid",
                "data": self._get_integrations_summary(),
            },
        ]
        return widgets

    def _get_house_mode(self) -> str:
        if self._house:
            return self._house.get_current_mode()
        return "inconnu"

    def _get_active_profile(self) -> dict:
        if self._profiles:
            profile = self._profiles.get_current_profile()
            if profile:
                return {"name": profile.name, "strategy": profile.strategy_type}
        return {"name": None, "strategy": None}

    def _get_alerts_summary(self) -> dict:
        return {"count": 0, "critical": 0}

    def _get_scenarios_summary(self) -> dict:
        if self._scenarios:
            scenarios = self._scenarios.get_all_scenarios()
            active = [s for s in scenarios if s.is_active]
            return {"total": len(scenarios), "active": len(active)}
        return {"total": 0, "active": 0}

    def _get_integrations_summary(self) -> List[dict]:
        return [
            {
                "name": adapter.get_adapter_name(),
                "status": adapter.get_status(),
            }
            for adapter in self._adapters
        ]
