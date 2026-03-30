"""Tests d'integration pour l'isolation des donnees par utilisateur - Iteration 7"""

import pytest
from infrastructure.auth.user_repository import UserDeviceRepository
from infrastructure.auth.service_locator import ServiceLocator, build_default_service_locator


@pytest.fixture(autouse=True)
def reset_locator():
    ServiceLocator.reset()
    yield
    ServiceLocator.reset()


class TestUserDeviceRepository:
    def test_add_device_stores_device(self):
        repo = UserDeviceRepository("user_1")
        device = repo.add_device("light-1", {"name": "Lampe salon"})
        assert device["name"] == "Lampe salon"

    def test_add_device_sets_owner_id(self):
        repo = UserDeviceRepository("user_1")
        device = repo.add_device("light-1", {"name": "Lampe"})
        assert device["owner_id"] == "user_1"

    def test_get_device_returns_stored(self):
        repo = UserDeviceRepository("user_1")
        repo.add_device("light-1", {"name": "Lampe"})
        found = repo.get_device("light-1")
        assert found is not None
        assert found["name"] == "Lampe"

    def test_get_device_unknown_returns_none(self):
        repo = UserDeviceRepository("user_1")
        assert repo.get_device("unknown") is None

    def test_get_all_returns_all_devices(self):
        repo = UserDeviceRepository("user_1")
        repo.add_device("d1", {"name": "D1"})
        repo.add_device("d2", {"name": "D2"})
        assert len(repo.get_all()) == 2

    def test_remove_device_returns_true(self):
        repo = UserDeviceRepository("user_1")
        repo.add_device("d1", {"name": "D1"})
        assert repo.remove_device("d1") is True
        assert repo.get_device("d1") is None

    def test_remove_device_unknown_returns_false(self):
        repo = UserDeviceRepository("user_1")
        assert repo.remove_device("unknown") is False

    def test_count_correct(self):
        repo = UserDeviceRepository("user_1")
        assert repo.count() == 0
        repo.add_device("d1", {})
        repo.add_device("d2", {})
        assert repo.count() == 2

    def test_clear_empties_repository(self):
        repo = UserDeviceRepository("user_1")
        repo.add_device("d1", {})
        repo.clear()
        assert repo.count() == 0


class TestDataIsolationBetweenUsers:
    def test_two_users_have_separate_repos(self):
        repo1 = UserDeviceRepository("user_1")
        repo2 = UserDeviceRepository("user_2")
        repo1.add_device("light-1", {"name": "Lampe user1"})
        assert repo2.get_device("light-1") is None

    def test_device_in_user1_not_visible_in_second_user(self):
        repo1 = UserDeviceRepository("user_1")
        repo2 = UserDeviceRepository("user_2")
        repo1.add_device("d1", {"name": "D1"})
        repo2.add_device("d2", {"name": "D2"})
        assert len(repo1.get_all()) == 1
        assert len(repo2.get_all()) == 1

    def test_service_locator_isolates_by_user(self):
        locator = build_default_service_locator()
        repo1 = locator.resolve_for_user("user_device_repository", "uid_1")
        repo2 = locator.resolve_for_user("user_device_repository", "uid_2")
        repo1.add_device("d1", {"name": "D1"})
        assert repo2.get_device("d1") is None

    def test_service_locator_same_user_shares_repo(self):
        locator = build_default_service_locator()
        repo1 = locator.resolve_for_user("user_device_repository", "uid_1")
        repo2 = locator.resolve_for_user("user_device_repository", "uid_1")
        repo1.add_device("d1", {"name": "D1"})
        assert repo2.get_device("d1") is not None

    def test_clear_context_resets_user_repo(self):
        locator = build_default_service_locator()
        repo = locator.resolve_for_user("user_device_repository", "uid_1")
        repo.add_device("d1", {"name": "D1"})
        locator.clear_user_context("uid_1")
        new_repo = locator.resolve_for_user("user_device_repository", "uid_1")
        assert new_repo.get_device("d1") is None

    def test_owner_id_matches_user_id(self):
        repo = UserDeviceRepository("specific_user")
        device = repo.add_device("d1", {"name": "D1"})
        assert device["owner_id"] == "specific_user"
