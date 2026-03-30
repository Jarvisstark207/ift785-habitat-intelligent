"""Tests unitaires pour le Service Locator Pattern - Iteration 7"""

import pytest
from infrastructure.auth.service_locator import ServiceLocator, build_default_service_locator
from infrastructure.auth.user_repository import UserDeviceRepository


@pytest.fixture(autouse=True)
def reset_locator():
    ServiceLocator.reset()
    yield
    ServiceLocator.reset()


@pytest.fixture
def locator():
    return ServiceLocator()


class TestServiceLocatorRegisterResolve:
    def test_register_and_resolve(self, locator):
        locator.register("my_service", lambda: {"value": 42})
        result = locator.resolve("my_service")
        assert result == {"value": 42}

    def test_resolve_unregistered_raises_key_error(self, locator):
        with pytest.raises(KeyError, match="non enregistre"):
            locator.resolve("unknown_service")

    def test_is_registered_true(self, locator):
        locator.register("svc", lambda: None)
        assert locator.is_registered("svc") is True

    def test_is_registered_false(self, locator):
        assert locator.is_registered("missing") is False

    def test_registered_services_lists_all(self, locator):
        locator.register("a", lambda: None)
        locator.register("b", lambda: None)
        services = locator.registered_services()
        assert "a" in services
        assert "b" in services

    def test_non_singleton_returns_different_instances(self, locator):
        locator.register("repo", lambda: [])
        r1 = locator.resolve("repo")
        r2 = locator.resolve("repo")
        assert r1 is not r2


class TestServiceLocatorSingleton:
    def test_singleton_returns_same_instance(self, locator):
        locator.register("svc", lambda: object(), singleton=True)
        s1 = locator.resolve("svc")
        s2 = locator.resolve("svc")
        assert s1 is s2

    def test_non_singleton_is_default(self, locator):
        locator.register("svc", lambda: object())
        s1 = locator.resolve("svc")
        s2 = locator.resolve("svc")
        assert s1 is not s2

    def test_singleton_flag_stored(self, locator):
        locator.register("svc", lambda: 99, singleton=True)
        assert locator.resolve("svc") == 99


class TestServiceLocatorUserScope:
    def test_resolve_for_user_returns_scoped_service(self, locator):
        locator.register("repo", lambda uid: UserDeviceRepository(uid))
        repo = locator.resolve_for_user("repo", "user_1")
        assert isinstance(repo, UserDeviceRepository)
        assert repo.user_id == "user_1"

    def test_resolve_for_user_same_user_same_instance(self, locator):
        locator.register("repo", lambda uid: UserDeviceRepository(uid))
        r1 = locator.resolve_for_user("repo", "user_1")
        r2 = locator.resolve_for_user("repo", "user_1")
        assert r1 is r2

    def test_resolve_for_user_different_users_different_instances(self, locator):
        locator.register("repo", lambda uid: UserDeviceRepository(uid))
        r1 = locator.resolve_for_user("repo", "user_1")
        r2 = locator.resolve_for_user("repo", "user_2")
        assert r1 is not r2

    def test_resolve_for_user_unregistered_raises(self, locator):
        with pytest.raises(KeyError):
            locator.resolve_for_user("missing", "user_1")

    def test_clear_user_context_removes_services(self, locator):
        locator.register("repo", lambda uid: UserDeviceRepository(uid))
        r1 = locator.resolve_for_user("repo", "user_1")
        locator.clear_user_context("user_1")
        r2 = locator.resolve_for_user("repo", "user_1")
        assert r1 is not r2

    def test_clear_user_context_unknown_user_no_error(self, locator):
        locator.clear_user_context("nonexistent")  # should not raise


class TestBuildDefaultServiceLocator:
    def test_builds_locator_with_auth_service(self):
        locator = build_default_service_locator()
        assert locator.is_registered("auth_service")

    def test_builds_locator_with_device_repository(self):
        locator = build_default_service_locator()
        assert locator.is_registered("user_device_repository")

    def test_resolve_user_device_repository_for_user(self):
        locator = build_default_service_locator()
        repo = locator.resolve_for_user("user_device_repository", "uid_1")
        assert isinstance(repo, UserDeviceRepository)
        assert repo.user_id == "uid_1"
