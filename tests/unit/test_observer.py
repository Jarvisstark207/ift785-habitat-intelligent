"""Tests unitaires - Pattern Observer"""

import pytest

from domain.patterns.observer import Observable, Observer
from domain.scenarios.scenario_manager import ScenarioManager


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

class ConcreteObserver(Observer):
    """Observer de test qui enregistre les notifications"""

    def __init__(self):
        self.received = []

    def update(self, event_type: str, data: dict) -> None:
        self.received.append({"event_type": event_type, "data": data})


class ConcreteObservable(Observable):
    """Observable de test"""

    def trigger(self, event_type: str, data: dict) -> None:
        self.notify(event_type, data)


# ---------------------------------------------------------------------------
# Tests Observer / Observable de base
# ---------------------------------------------------------------------------

class TestObserver:

    def test_observer_recoit_notification(self):
        """Un observer abonne recoit bien la notification"""
        observable = ConcreteObservable()
        observer = ConcreteObserver()

        observable.subscribe(observer)
        observable.trigger("temperature", {"value": 27.0})

        assert len(observer.received) == 1
        assert observer.received[0]["event_type"] == "temperature"

    def test_observer_non_abonne_ne_recoit_pas(self):
        """Un observer non abonne ne recoit rien"""
        observable = ConcreteObservable()
        observer = ConcreteObserver()

        observable.trigger("temperature", {"value": 27.0})

        assert len(observer.received) == 0

    def test_subscribe_multiple_observers(self):
        """Plusieurs observers recoivent tous la notification"""
        observable = ConcreteObservable()
        obs1 = ConcreteObserver()
        obs2 = ConcreteObserver()

        observable.subscribe(obs1)
        observable.subscribe(obs2)
        observable.trigger("motion", {"value": 1})

        assert len(obs1.received) == 1
        assert len(obs2.received) == 1

    def test_unsubscribe_arrete_les_notifications(self):
        """Un observer desabonne ne recoit plus de notifications"""
        observable = ConcreteObservable()
        observer = ConcreteObserver()

        observable.subscribe(observer)
        observable.unsubscribe(observer)
        observable.trigger("temperature", {"value": 30.0})

        assert len(observer.received) == 0

    def test_subscribe_meme_observer_une_seule_fois(self):
        """Abonner le meme observer deux fois ne l'ajoute qu'une fois"""
        observable = ConcreteObservable()
        observer = ConcreteObserver()

        observable.subscribe(observer)
        observable.subscribe(observer)

        assert observable.get_observer_count() == 1

    def test_get_observer_count(self):
        """Le compteur d'observers est correct"""
        observable = ConcreteObservable()
        obs1 = ConcreteObserver()
        obs2 = ConcreteObserver()

        assert observable.get_observer_count() == 0
        observable.subscribe(obs1)
        assert observable.get_observer_count() == 1
        observable.subscribe(obs2)
        assert observable.get_observer_count() == 2

    def test_notify_avec_donnees_complexes(self):
        """L'observer recoit bien les donnees transmises"""
        observable = ConcreteObservable()
        observer = ConcreteObserver()
        observable.subscribe(observer)

        data = {"value": 27.5, "location": "salon", "unit": "C"}
        observable.trigger("temperature", data)

        assert observer.received[0]["data"] == data

    def test_plusieurs_notifications_successives(self):
        """L'observer recoit plusieurs notifications successives"""
        observable = ConcreteObservable()
        observer = ConcreteObserver()
        observable.subscribe(observer)

        observable.trigger("temperature", {"value": 25.0})
        observable.trigger("motion", {"value": 1})
        observable.trigger("temperature", {"value": 26.0})

        assert len(observer.received) == 3

    def test_unsubscribe_observer_absent_sans_erreur(self):
        """Desabonner un observer non inscrit ne leve pas d'exception"""
        observable = ConcreteObservable()
        observer = ConcreteObserver()

        observable.unsubscribe(observer)  # pas d'erreur


# ---------------------------------------------------------------------------
# Tests ScenarioManager (Observable concret)
# ---------------------------------------------------------------------------

class TestScenarioManagerObserver:

    @pytest.fixture
    def manager(self):
        return ScenarioManager()

    @pytest.fixture
    def observer(self):
        return ConcreteObserver()

    def test_creation_scenario_notifie_observer(self, manager, observer):
        """La creation d'un scenario notifie les observers"""
        manager.subscribe(observer)
        manager.create_scenario(
            name="Test",
            conditions=[{"trigger_type": "temperature", "operator": ">", "value": 25}],
            actions=[{"device_id": "fan_01", "action": "turn_on"}],
        )
        assert len(observer.received) == 1
        assert observer.received[0]["event_type"] == "scenario_created"

    def test_execution_scenario_notifie_observer(self, manager, observer):
        """L'execution d'un scenario notifie les observers"""
        scenario = manager.create_scenario(
            name="Test exec",
            conditions=[{"trigger_type": "temperature", "operator": ">", "value": 25}],
            actions=[{"device_id": "fan_01", "action": "turn_on"}],
        )
        manager.subscribe(observer)
        manager.execute_scenario(scenario.id)

        events = [r["event_type"] for r in observer.received]
        assert "scenario_executed" in events

    def test_suppression_scenario_notifie_observer(self, manager, observer):
        """La suppression d'un scenario notifie les observers"""
        scenario = manager.create_scenario(
            name="Delete test",
            conditions=[{"trigger_type": "motion", "operator": "==", "value": 1}],
            actions=[{"device_id": "light_01", "action": "turn_on"}],
        )
        manager.subscribe(observer)
        manager.delete_scenario(scenario.id)

        events = [r["event_type"] for r in observer.received]
        assert "scenario_deleted" in events
