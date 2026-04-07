"""
Tests unitaires - EventBus + @on_event (Itération 9 : AOP)
"""

import asyncio
import pytest

from app.core.event_bus import EventBus, on_event


def run(coro):
    return asyncio.get_event_loop().run_until_complete(coro)


@pytest.fixture(autouse=True)
def fresh_bus():
    """Recrée un bus propre avant chaque test."""
    EventBus.reset()
    yield
    EventBus.reset()


# ---------------------------------------------------------------------------
# Singleton
# ---------------------------------------------------------------------------

class TestEventBusSingleton:
    def test_instance_is_singleton(self):
        a = EventBus.instance()
        b = EventBus.instance()
        assert a is b

    def test_reset_creates_new_instance(self):
        a = EventBus.instance()
        EventBus.reset()
        b = EventBus.instance()
        assert a is not b


# ---------------------------------------------------------------------------
# Subscribe / Unsubscribe
# ---------------------------------------------------------------------------

class TestEventBusSubscribe:
    def test_subscribe_adds_handler(self):
        bus = EventBus.instance()
        called = []

        def handler(event, payload):
            called.append(event)

        bus.subscribe("test.event", handler)
        assert handler in bus.subscribers("test.event")

    def test_subscribe_same_handler_once(self):
        bus = EventBus.instance()

        def handler(event, payload):
            pass

        bus.subscribe("test.event", handler)
        bus.subscribe("test.event", handler)
        assert bus.subscribers("test.event").count(handler) == 1

    def test_unsubscribe_removes_handler(self):
        bus = EventBus.instance()
        called = []

        def handler(event, payload):
            called.append(event)

        bus.subscribe("test.event", handler)
        bus.unsubscribe("test.event", handler)
        bus.publish("test.event", {})
        assert called == []

    def test_subscribers_empty_for_unknown_event(self):
        bus = EventBus.instance()
        assert bus.subscribers("unknown.event") == []


# ---------------------------------------------------------------------------
# Publish
# ---------------------------------------------------------------------------

class TestEventBusPublish:
    def test_publish_calls_handler(self):
        bus = EventBus.instance()
        received = []

        def handler(event, payload):
            received.append((event, payload))

        bus.subscribe("device.updated", handler)
        bus.publish("device.updated", {"id": 1})
        assert received == [("device.updated", {"id": 1})]

    def test_publish_calls_multiple_handlers(self):
        bus = EventBus.instance()
        results = []

        def handler_a(event, payload):
            results.append("A")

        def handler_b(event, payload):
            results.append("B")

        bus.subscribe("my.event", handler_a)
        bus.subscribe("my.event", handler_b)
        bus.publish("my.event", {})
        assert "A" in results and "B" in results

    def test_publish_no_subscribers_no_error(self):
        bus = EventBus.instance()
        bus.publish("ghost.event", {"x": 1})  # should not raise

    def test_publish_swallows_handler_exceptions(self):
        bus = EventBus.instance()

        def bad_handler(event, payload):
            raise RuntimeError("handler crash")

        bus.subscribe("bad.event", bad_handler)
        bus.publish("bad.event", {})  # should not raise

    def test_publish_stores_in_history(self):
        bus = EventBus.instance()
        bus.publish("log.event", {"msg": "hello"})
        history = bus.get_history()
        assert any(e["event"] == "log.event" for e in history)

    def test_history_records_payload(self):
        bus = EventBus.instance()
        bus.publish("sensor.alert", {"temp": 99})
        history = bus.get_history()
        entry = next(e for e in history if e["event"] == "sensor.alert")
        assert entry["payload"] == {"temp": 99}

    def test_clear_history(self):
        bus = EventBus.instance()
        bus.publish("x.event", {})
        bus.clear_history()
        assert bus.get_history() == []


# ---------------------------------------------------------------------------
# @on_event decorator
# ---------------------------------------------------------------------------

class TestOnEventDecorator:
    def test_on_event_subscribes_handler(self):
        bus = EventBus.instance()

        @on_event("device.created")
        def handler(event, payload):
            pass

        assert handler in bus.subscribers("device.created")

    def test_on_event_preserves_function_name(self):
        @on_event("x.event")
        def my_handler(event, payload):
            pass

        assert my_handler.__name__ == "my_handler"

    def test_on_event_stores_event_name(self):
        @on_event("sensor.alert")
        def handler(event, payload):
            pass

        assert handler._on_event == "sensor.alert"

    def test_on_event_called_on_publish(self):
        bus = EventBus.instance()
        received = []

        @on_event("user.login")
        def handle_login(event, payload):
            received.append(payload)

        bus.publish("user.login", {"user": "alice"})
        assert received == [{"user": "alice"}]

    def test_on_event_multiple_events(self):
        bus = EventBus.instance()
        log = []

        @on_event("ev.one")
        def h1(event, payload):
            log.append("one")

        @on_event("ev.two")
        def h2(event, payload):
            log.append("two")

        bus.publish("ev.one", {})
        bus.publish("ev.two", {})
        assert "one" in log and "two" in log

