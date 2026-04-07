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

