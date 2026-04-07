"""
Tests d'intégration - EventBus flow complet (Itération 9 : AOP)
Teste la chaîne complète publish → handler → effets observables.
"""

import pytest

from app.core.event_bus import EventBus, on_event
from app.core.aspects import invalidate_cache, aspect_cache


@pytest.fixture(autouse=True)
def fresh_bus():
    EventBus.reset()
    invalidate_cache()
    yield
    EventBus.reset()
    invalidate_cache()


# ---------------------------------------------------------------------------
# Flux publish → handler
# ---------------------------------------------------------------------------

class TestEventBusFlowPublish:
    def test_publish_and_receive_device_created(self):
        bus = EventBus.instance()
        received = []

        def on_device_created(event, payload):
            received.append(payload)

        bus.subscribe("device.created", on_device_created)
        bus.publish("device.created", {"id": "dev-001", "name": "Sensor A"})

        assert len(received) == 1
        assert received[0]["id"] == "dev-001"

    def test_publish_and_receive_sensor_alert(self):
        bus = EventBus.instance()
        alerts = []

        def on_alert(event, payload):
            alerts.append(payload)

        bus.subscribe("sensor.alert", on_alert)
        bus.publish("sensor.alert", {"type": "temperature", "value": 99})

        assert len(alerts) == 1
        assert alerts[0]["value"] == 99

    def test_publish_multiple_events(self):
        bus = EventBus.instance()
        log = []

        def handler(event, payload):
            log.append(event)

        bus.subscribe("ev.a", handler)
        bus.subscribe("ev.b", handler)
        bus.publish("ev.a", {})
        bus.publish("ev.b", {})

        assert "ev.a" in log
        assert "ev.b" in log

    def test_chain_of_handlers(self):
        bus = EventBus.instance()
        pipeline = []

        def step_one(event, payload):
            pipeline.append("step1")

        def step_two(event, payload):
            pipeline.append("step2")

        def step_three(event, payload):
            pipeline.append("step3")

        bus.subscribe("pipeline.event", step_one)
        bus.subscribe("pipeline.event", step_two)
        bus.subscribe("pipeline.event", step_three)
        bus.publish("pipeline.event", {})

        assert pipeline == ["step1", "step2", "step3"]

    def test_handler_exception_does_not_block_next_handler(self):
        bus = EventBus.instance()
        results = []

        def bad_handler(event, payload):
            raise RuntimeError("crash")

        def good_handler(event, payload):
            results.append("ok")

        bus.subscribe("mixed.event", bad_handler)
        bus.subscribe("mixed.event", good_handler)
        bus.publish("mixed.event", {})

        assert results == ["ok"]


# ---------------------------------------------------------------------------
# Flux @on_event déclaratif
# ---------------------------------------------------------------------------

class TestEventBusFlowDeclarative:
    def test_declarative_subscriber_receives_event(self):
        received = []

        @on_event("status.changed")
        def handle_status(event, payload):
            received.append(payload)

        EventBus.instance().publish("status.changed", {"status": "active"})
        assert len(received) == 1
        assert received[0]["status"] == "active"

    def test_multiple_declarative_subscribers(self):
        log = []

        @on_event("multi.event")
        def subscriber_one(event, payload):
            log.append("one")

        @on_event("multi.event")
        def subscriber_two(event, payload):
            log.append("two")

        EventBus.instance().publish("multi.event", {})
        assert "one" in log and "two" in log

    def test_history_grows_with_events(self):
        bus = EventBus.instance()
        bus.publish("h.event", {"n": 1})
        bus.publish("h.event", {"n": 2})
        bus.publish("h.event", {"n": 3})
        history = bus.get_history()
        assert len([e for e in history if e["event"] == "h.event"]) == 3


# ---------------------------------------------------------------------------
# Flux EventBus → invalidation du cache
# ---------------------------------------------------------------------------

class TestEventBusFlowCacheInvalidation:
    def test_event_triggers_cache_invalidation(self):
        call_count = [0]

        @aspect_cache(ttl=60, key_fn=lambda: "devices:summary")
        def get_summary():
            call_count[0] += 1
            return {"total": call_count[0]}

        bus = EventBus.instance()

        def invalidate_on_device_event(event, payload):
            invalidate_cache(prefix="devices:")

        bus.subscribe("device.created", invalidate_on_device_event)

        get_summary()
        assert call_count[0] == 1

        get_summary()
        assert call_count[0] == 1  # from cache

        bus.publish("device.created", {"id": "new"})
        get_summary()
        assert call_count[0] == 2  # cache invalidated

    def test_unrelated_event_does_not_invalidate_cache(self):
        call_count = [0]

        @aspect_cache(ttl=60, key_fn=lambda: "sensors:latest")
        def get_sensors():
            call_count[0] += 1
            return {"count": call_count[0]}

        bus = EventBus.instance()

        def invalidate_devices(event, payload):
            invalidate_cache(prefix="devices:")

        bus.subscribe("device.created", invalidate_devices)

        get_sensors()
        bus.publish("device.created", {})
        get_sensors()

        assert call_count[0] == 1  # sensors cache not invalidated
