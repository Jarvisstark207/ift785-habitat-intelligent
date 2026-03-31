"""
Tests unitaires - DI Container avec introspection (Itération 8)
Couvre la résolution automatique via inspect.signature et get_type_hints.
"""

import pytest
from infrastructure.di.container import DIContainer


# ---------------------------------------------------------------------------
# Stubs pour les tests
# ---------------------------------------------------------------------------

class FakeDB:
    def __init__(self):
        self.connected = True


class FakeCache:
    def __init__(self):
        self.data = {}


class FakeRepository:
    def __init__(self, db: FakeDB):
        self.db = db


class FakeService:
    def __init__(self, repo: FakeRepository, cache: FakeCache):
        self.repo = repo
        self.cache = cache


class SimpleService:
    def __init__(self):
        self.value = 99


class ServiceWithOptionalDep:
    def __init__(self, name: str = "default"):
        self.name = name


# ---------------------------------------------------------------------------
# Compatibilité legacy (résolution par nom)
# ---------------------------------------------------------------------------

class TestDIContainerLegacy:
    def test_register_and_resolve_by_name(self):
        c = DIContainer()
        c.register("greeting", lambda: "hello")
        assert c.resolve("greeting") == "hello"

    def test_resolve_unknown_name_raises_keyerror(self):
        c = DIContainer()
        with pytest.raises(KeyError):
            c.resolve("nonexistent")

    def test_singleton_by_name(self):
        c = DIContainer()
        c.register("svc", lambda: [], singleton=True)
        a = c.resolve("svc")
        b = c.resolve("svc")
        assert a is b

    def test_transient_by_name(self):
        c = DIContainer()
        c.register("svc", lambda: [])
        assert c.resolve("svc") is not c.resolve("svc")

    def test_is_registered_by_name(self):
        c = DIContainer()
        c.register("x", lambda: None)
        assert c.is_registered("x") is True
        assert c.is_registered("y") is False

    def test_registered_services_list(self):
        c = DIContainer()
        c.register("a", lambda: None)
        c.register("b", lambda: None)
        services = c.registered_services()
        assert "a" in services
        assert "b" in services


# ---------------------------------------------------------------------------
# Résolution par introspection de type
# ---------------------------------------------------------------------------

class TestDIContainerIntrospection:
    def test_resolve_simple_type_no_deps(self):
        c = DIContainer()
        c.register(FakeDB, FakeDB)
        db = c.resolve(FakeDB)
        assert isinstance(db, FakeDB)
        assert db.connected is True

    def test_resolve_by_type_hints(self):
        c = DIContainer()
        c.register(FakeDB, FakeDB)
        c.register(FakeRepository, FakeRepository)
        repo = c.resolve(FakeRepository)
        assert isinstance(repo, FakeRepository)
        assert isinstance(repo.db, FakeDB)

    def test_resolve_chain_of_dependencies(self):
        c = DIContainer()
        c.register(FakeDB, FakeDB)
        c.register(FakeCache, FakeCache)
        c.register(FakeRepository, FakeRepository)
        c.register(FakeService, FakeService)
        service = c.resolve(FakeService)
        assert isinstance(service, FakeService)
        assert isinstance(service.repo, FakeRepository)
        assert isinstance(service.cache, FakeCache)
        assert isinstance(service.repo.db, FakeDB)

    def test_is_registered_by_type(self):
        c = DIContainer()
        c.register(FakeDB, FakeDB)
        assert c.is_registered(FakeDB) is True
        assert c.is_registered(FakeCache) is False

    def test_missing_dependency_raises_valueerror(self):
        c = DIContainer()
        c.register(FakeRepository, FakeRepository)
        # FakeDB not registered
        with pytest.raises(ValueError):
            c.resolve(FakeRepository)

    def test_resolve_uses_registered_implementation(self):
        class AbstractRepo:
            pass

        class ConcreteRepo(AbstractRepo):
            def __init__(self):
                self.impl = "concrete"

        c = DIContainer()
        c.register(AbstractRepo, ConcreteRepo)
        repo = c.resolve(AbstractRepo)
        assert isinstance(repo, ConcreteRepo)
        assert repo.impl == "concrete"

    def test_resolve_uses_mock_for_tests(self):
        class RealRepo:
            def __init__(self):
                self.real = True

        class FakeRepoMock:
            def __init__(self):
                self.real = False

        c = DIContainer()
        c.register(RealRepo, FakeRepoMock)
        repo = c.resolve(RealRepo)
        assert isinstance(repo, FakeRepoMock)
        assert repo.real is False

    def test_optional_deps_with_defaults_skipped(self):
        c = DIContainer()
        c.register(ServiceWithOptionalDep, ServiceWithOptionalDep)
        svc = c.resolve(ServiceWithOptionalDep)
        assert isinstance(svc, ServiceWithOptionalDep)
        assert svc.name == "default"

    def test_inspect_signature_used(self):
        import inspect
        sig = inspect.signature(FakeService.__init__)
        params = list(sig.parameters.keys())
        assert "repo" in params
        assert "cache" in params

    def test_get_type_hints_used(self):
        from typing import get_type_hints
        hints = get_type_hints(FakeService.__init__)
        assert hints.get("repo") is FakeRepository
        assert hints.get("cache") is FakeCache

    def test_resolve_returns_new_instance_each_time(self):
        c = DIContainer()
        c.register(FakeDB, FakeDB)
        a = c.resolve(FakeDB)
        b = c.resolve(FakeDB)
        assert a is not b
