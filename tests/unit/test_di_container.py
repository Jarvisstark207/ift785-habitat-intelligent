"""
Tests unitaires pour le DI Container - Iteration 6
"""

import pytest
from infrastructure.di.container import DIContainer


@pytest.fixture
def container():
    return DIContainer()


class TestDIContainerRegister:
    def test_register_and_is_registered(self, container):
        container.register("my_service", lambda: "value")
        assert container.is_registered("my_service") is True

    def test_unregistered_service(self, container):
        assert container.is_registered("unknown") is False

    def test_registered_services_list(self, container):
        container.register("svc_a", lambda: "a")
        container.register("svc_b", lambda: "b")
        services = container.registered_services()
        assert "svc_a" in services
        assert "svc_b" in services

    def test_register_overwrite(self, container):
        container.register("svc", lambda: "first")
        container.register("svc", lambda: "second")
        assert container.resolve("svc") == "second"


class TestDIContainerResolve:
    def test_resolve_simple_service(self, container):
        container.register("greeting", lambda: "hello")
        result = container.resolve("greeting")
        assert result == "hello"

    def test_resolve_unregistered_raises(self, container):
        with pytest.raises(KeyError):
            container.resolve("nonexistent")

    def test_resolve_returns_new_instance_each_time(self, container):
        container.register("list_svc", lambda: [])
        a = container.resolve("list_svc")
        b = container.resolve("list_svc")
        assert a is not b

    def test_resolve_with_class_factory(self, container):
        class MyService:
            def __init__(self):
                self.value = 42

        container.register("my_service", MyService)
        result = container.resolve("my_service")
        assert isinstance(result, MyService)
        assert result.value == 42


class TestDIContainerSingleton:
    def test_singleton_returns_same_instance(self, container):
        container.register("singleton_svc", lambda: [], singleton=True)
        a = container.resolve("singleton_svc")
        b = container.resolve("singleton_svc")
        assert a is b

    def test_non_singleton_returns_different_instances(self, container):
        container.register("transient_svc", lambda: [])
        a = container.resolve("transient_svc")
        b = container.resolve("transient_svc")
        assert a is not b

    def test_singleton_vs_transient(self, container):
        container.register("s", lambda: object(), singleton=True)
        container.register("t", lambda: object())
        s1 = container.resolve("s")
        s2 = container.resolve("s")
        t1 = container.resolve("t")
        t2 = container.resolve("t")
        assert s1 is s2
        assert t1 is not t2


class TestDIContainerWithDependencies:
    def test_resolve_dependency_chain(self, container):
        container.register("db", lambda: {"type": "sqlite"}, singleton=True)
        container.register(
            "repo",
            lambda: {"db": container.resolve("db"), "name": "DeviceRepository"}
        )
        container.register(
            "service",
            lambda: {"repo": container.resolve("repo"), "name": "DeviceService"}
        )
        service = container.resolve("service")
        assert service["name"] == "DeviceService"
        assert service["repo"]["name"] == "DeviceRepository"
        assert service["repo"]["db"]["type"] == "sqlite"

    def test_multiple_services(self, container):
        container.register("svc1", lambda: "service1")
        container.register("svc2", lambda: "service2")
        container.register("svc3", lambda: "service3")
        assert len(container.registered_services()) == 3
        assert container.resolve("svc1") == "service1"
        assert container.resolve("svc2") == "service2"
        assert container.resolve("svc3") == "service3"
