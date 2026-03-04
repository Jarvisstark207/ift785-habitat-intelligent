"""Tests d'integration - Scenarios automatises (Observer + Scenario)"""

import pytest

from domain.scenarios.scenario_manager import ScenarioManager
from domain.scenarios.scenario import Scenario
from domain.patterns.observer import Observer


class EventLogger(Observer):
    """Observer qui enregistre tous les evenements"""

    def __init__(self):
        self.events = []

    def update(self, event_type: str, data: dict) -> None:
        self.events.append({"type": event_type, "data": data})


@pytest.fixture
def manager():
    return ScenarioManager()


@pytest.fixture
def logger():
    return EventLogger()


@pytest.fixture
def scenario_temperature(manager):
    """Scenario: si temperature > 26 alors activer ventilateur"""
    return manager.create_scenario(
        name="Refroidissement",
        conditions=[
            {"trigger_type": "temperature", "operator": ">", "value": 26.0}
        ],
        actions=[
            {"device_id": "fan_01", "action": "turn_on", "parameters": {"speed": "medium"}}
        ],
        description="Activation automatique du ventilateur",
    )


class TestScenarioCRUD:

    def test_creation_scenario_retourne_objet(self, manager):
        """La creation d'un scenario retourne un objet Scenario valide"""
        scenario = manager.create_scenario(
            name="Test",
            conditions=[{"trigger_type": "motion", "operator": "==", "value": 1}],
            actions=[{"device_id": "light_01", "action": "turn_on"}],
        )
        assert isinstance(scenario, Scenario)
        assert scenario.name == "Test"

    def test_scenario_accessible_par_id(self, manager, scenario_temperature):
        """Un scenario cree est retrouvable par son ID"""
        found = manager.get_scenario(scenario_temperature.id)
        assert found is not None
        assert found.id == scenario_temperature.id

    def test_liste_scenarios(self, manager, scenario_temperature):
        """get_all_scenarios retourne tous les scenarios crees"""
        manager.create_scenario(
            name="Second",
            conditions=[{"trigger_type": "motion", "operator": "==", "value": 1}],
            actions=[{"device_id": "light_02", "action": "turn_off"}],
        )
        scenarios = manager.get_all_scenarios()
        assert len(scenarios) >= 2

    def test_suppression_scenario(self, manager, scenario_temperature):
        """La suppression d'un scenario le retire de la liste"""
        scenario_id = scenario_temperature.id
        result = manager.delete_scenario(scenario_id)
        assert result is True
        assert manager.get_scenario(scenario_id) is None

    def test_activation_desactivation(self, manager, scenario_temperature):
        """Un scenario peut etre active et desactive"""
        manager.deactivate_scenario(scenario_temperature.id)
        assert scenario_temperature.is_active is False

        manager.activate_scenario(scenario_temperature.id)
        assert scenario_temperature.is_active is True


class TestScenarioExecution:

    def test_execution_manuelle_scenario(self, manager, scenario_temperature):
        """L'execution manuelle d'un scenario retourne un resultat"""
        result = manager.execute_scenario(scenario_temperature.id)
        assert result is not None
        assert result["scenario_id"] == scenario_temperature.id

    def test_execution_incremente_log(self, manager, scenario_temperature):
        """Chaque execution est enregistree dans le log"""
        manager.execute_scenario(scenario_temperature.id)
        manager.execute_scenario(scenario_temperature.id)
        assert len(scenario_temperature.execution_log) == 2

    def test_execution_scenario_inexistant_retourne_none(self, manager):
        """Executer un scenario inexistant retourne None"""
        result = manager.execute_scenario("id-inexistant")
        assert result is None


class TestScenarioDeclenchement:

    def test_evenement_declenche_scenario_actif(self, manager, scenario_temperature):
        """Un evenement temperature > 26 declenche le scenario"""
        triggered = manager.process_event(
            "temperature", {"value": 27.5, "location": "salon"}
        )
        assert len(triggered) == 1
        assert triggered[0]["scenario_id"] == scenario_temperature.id

    def test_evenement_sous_seuil_ne_declenche_pas(self, manager, scenario_temperature):
        """Un evenement temperature < seuil ne declenche pas le scenario"""
        triggered = manager.process_event(
            "temperature", {"value": 24.0, "location": "salon"}
        )
        assert len(triggered) == 0

    def test_scenario_inactif_non_declenche(self, manager, scenario_temperature):
        """Un scenario desactive n'est pas declenche"""
        manager.deactivate_scenario(scenario_temperature.id)
        triggered = manager.process_event(
            "temperature", {"value": 30.0, "location": "salon"}
        )
        assert len(triggered) == 0

    def test_observer_notifie_lors_declenchement(self, manager, logger, scenario_temperature):
        """L'observer est notifie quand un scenario est declenche"""
        manager.subscribe(logger)
        manager.process_event("temperature", {"value": 28.0})
        events = [e["type"] for e in logger.events]
        assert "scenario_triggered" in events

    def test_conditions_multiples_evaluees(self, manager):
        """Un scenario avec plusieurs conditions verifie chaque condition"""
        scenario = manager.create_scenario(
            name="Multi-condition",
            conditions=[
                {"trigger_type": "temperature", "operator": ">", "value": 25},
                {"trigger_type": "temperature", "operator": ">", "value": 28},
            ],
            actions=[{"device_id": "fan_01", "action": "turn_on"}],
        )
        # La premiere condition suffit a declencher
        triggered = manager.process_event("temperature", {"value": 26.0})
        assert any(t["scenario_id"] == scenario.id for t in triggered)
