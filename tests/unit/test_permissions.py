"""Tests unitaires pour les permissions et le RBAC - Iteration 7"""

import pytest
from fastapi import HTTPException
from app.core.provided_auth import (
    User, ROLE_HIERARCHY, ROLES,
    require_minimum_role, make_test_user,
)
from application.services.auth_service import AuthService
from domain.auth.user_store import UserStore


@pytest.fixture(autouse=True)
def reset_store():
    UserStore.reset()
    yield
    UserStore.reset()


class TestRoleHierarchy:
    def test_admin_level_is_3(self):
        assert ROLE_HIERARCHY["admin"] == 3

    def test_user_level_is_2(self):
        assert ROLE_HIERARCHY["user"] == 2

    def test_guest_level_is_1(self):
        assert ROLE_HIERARCHY["guest"] == 1

    def test_admin_greater_than_user(self):
        assert ROLE_HIERARCHY["admin"] > ROLE_HIERARCHY["user"]

    def test_user_greater_than_guest(self):
        assert ROLE_HIERARCHY["user"] > ROLE_HIERARCHY["guest"]

    def test_roles_set_contains_three_roles(self):
        assert ROLES == {"admin", "user", "guest"}


class TestRequireMinimumRole:
    def test_admin_passes_admin_check(self):
        user = make_test_user(role="admin")
        require_minimum_role(user, "admin")  # should not raise

    def test_admin_passes_user_check(self):
        user = make_test_user(role="admin")
        require_minimum_role(user, "user")  # admin >= user

    def test_admin_passes_guest_check(self):
        user = make_test_user(role="admin")
        require_minimum_role(user, "guest")

    def test_user_passes_user_check(self):
        user = make_test_user(role="user")
        require_minimum_role(user, "user")

    def test_user_passes_guest_check(self):
        user = make_test_user(role="user")
        require_minimum_role(user, "guest")

    def test_user_fails_admin_check(self):
        user = make_test_user(role="user")
        with pytest.raises(HTTPException) as exc:
            require_minimum_role(user, "admin")
        assert exc.value.status_code == 403

    def test_guest_fails_user_check(self):
        user = make_test_user(role="guest")
        with pytest.raises(HTTPException) as exc:
            require_minimum_role(user, "user")
        assert exc.value.status_code == 403

    def test_guest_fails_admin_check(self):
        user = make_test_user(role="guest")
        with pytest.raises(HTTPException) as exc:
            require_minimum_role(user, "admin")
        assert exc.value.status_code == 403

    def test_unknown_role_raises_value_error(self):
        user = make_test_user(role="user")
        with pytest.raises(ValueError, match="Role inconnu"):
            require_minimum_role(user, "superadmin")

    def test_error_message_contains_roles(self):
        user = make_test_user(role="guest")
        with pytest.raises(HTTPException) as exc:
            require_minimum_role(user, "admin")
        assert "403" in str(exc.value.status_code)


class TestUserPermissions:
    def test_admin_has_all_permissions(self):
        store = UserStore.get_instance()
        user = store.register("adm", "pwd", "admin")
        assert "device:delete" in user.permissions
        assert "user:write" in user.permissions

    def test_user_has_read_write_device(self):
        store = UserStore.get_instance()
        user = store.register("usr", "pwd", "user")
        assert "device:read" in user.permissions
        assert "device:write" in user.permissions
        assert "device:delete" not in user.permissions

    def test_guest_has_only_read(self):
        store = UserStore.get_instance()
        user = store.register("gst", "pwd", "guest")
        assert user.permissions == ["device:read"]

    def test_get_user_permissions_via_service(self):
        service = AuthService()
        user = service.register("bob", "pwd", "user")
        perms = service.get_user_permissions(user.user_id)
        assert "device:read" in perms

    def test_get_permissions_unknown_user_returns_empty(self):
        service = AuthService()
        perms = service.get_user_permissions("nonexistent-id")
        assert perms == []

    def test_has_role_returns_true_for_equal_role(self):
        user = User(id="u", role="user")
        assert user.has_role("user") is True

    def test_has_role_returns_false_for_higher_role(self):
        user = User(id="u", role="user")
        assert user.has_role("admin") is False
