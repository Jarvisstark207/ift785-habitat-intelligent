"""Gestionnaire de scenarios - utilise le pattern Observer"""

from typing import Dict, List, Optional

from domain.patterns.observer import Observable
from domain.scenarios.scenario import Scenario, ScenarioAction, ScenarioCondition


class ScenarioManager(Observable):
    """Gestionnaire de scenarios automatises.

    Utilise le pattern Observer pour notifier les abonnes
    lors des creations, activations et executions de scenarios.
    """

    def __init__(self) -> None:
        super().__init__()
        self._scenarios: Dict[str, Scenario] = {}

    def create_scenario(
        self,
        name: str,
        conditions: List[dict],
        actions: List[dict],
        description: str = "",
    ) -> Scenario:
        """Cree et enregistre un nouveau scenario"""
        conds = [
            ScenarioCondition(
                trigger_type=c["trigger_type"],
                operator=c["operator"],
                value=float(c["value"]),
            )
            for c in conditions
        ]
        acts = [
            ScenarioAction(
                device_id=a["device_id"],
                action=a["action"],
                parameters=a.get("parameters", {}),
            )
            for a in actions
        ]
        scenario = Scenario(
            name=name,
            description=description,
            conditions=conds,
            actions=acts,
        )
        self._scenarios[scenario.id] = scenario
        self.notify("scenario_created", scenario.to_dict())
        return scenario

    def get_scenario(self, scenario_id: str) -> Optional[Scenario]:
        """Retourne un scenario par ID"""
        return self._scenarios.get(scenario_id)

    def get_all_scenarios(self) -> List[Scenario]:
        """Retourne tous les scenarios"""
        return list(self._scenarios.values())

    def activate_scenario(self, scenario_id: str) -> bool:
        """Active un scenario"""
        scenario = self._scenarios.get(scenario_id)
        if scenario:
            scenario.is_active = True
            self.notify("scenario_activated", {"id": scenario_id})
            return True
        return False

    def deactivate_scenario(self, scenario_id: str) -> bool:
        """Desactive un scenario"""
        scenario = self._scenarios.get(scenario_id)
        if scenario:
            scenario.is_active = False
            self.notify("scenario_deactivated", {"id": scenario_id})
            return True
        return False

    def delete_scenario(self, scenario_id: str) -> bool:
        """Supprime un scenario"""
        if scenario_id in self._scenarios:
            del self._scenarios[scenario_id]
            self.notify("scenario_deleted", {"id": scenario_id})
            return True
        return False

    def execute_scenario(self, scenario_id: str) -> Optional[dict]:
        """Execute un scenario manuellement"""
        scenario = self._scenarios.get(scenario_id)
        if not scenario:
            return None
        result = scenario.execute()
        self.notify("scenario_executed", result)
        return result

    def process_event(self, event_type: str, data: dict) -> List[dict]:
        """Traite un evenement et declenche les scenarios correspondants"""
        triggered = []
        event_value = data.get("value", 0)
        for scenario in self._scenarios.values():
            if not scenario.is_active:
                continue
            for condition in scenario.conditions:
                if condition.trigger_type == event_type:
                    if condition.evaluate(float(event_value)):
                        result = scenario.execute()
                        triggered.append(result)
                        self.notify("scenario_triggered", result)
                        break
        return triggered
