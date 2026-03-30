"""Tests d'integration multi-utilisateurs - Iteration 7"""

import pytest
from application.services.auth_service import AuthService
from domain.auth.user_store import UserStore
from fastapi import HTTPException
from app.core.provided_auth import require_minimum_role, make_test_user


@pytest.fixture(autouse=True)
def reset():
    UserStore.reset()
    yield
    UserStore.reset()


@pytest.fixture
def service():
    return AuthService()


class TestMultiUserRegistration:
    def test_register_three_different_roles(self, service):
        a = service.register("alice", "pwd", "admin")
        b = service.register("bob", "pwd", "user")
        c = service.register("carol", "pwd", "guest")
        assert a.role == "admin"
        assert b.role == "user"
        assert c.role == "guest"

    def test_each_user_has_unique_id(self, service):
        u1 = service.register("u1", "pwd")
        u2 = service.register("u2", "pwd")
        assert u1.user_id != u2.user_id

    def test_get_all_returns_all_registered(self, service):
        service.register("u1", "pwd")
        service.register("u2", "pwd")
        service.register("u3", "pwd")
        users = service.get_all_users()
        assert len(users) == 3

    def test_register_same_username_twice_raises(self, service):
        service.register("alice", "pwd")
        with pytest.raises(ValueError):
            service.register("alice", "other")


class TestMultiUserLogin:
    def test_each_user_gets_own_token(self, service):
        service.register("alice", "p1")
        service.register("bob", "p2")
        t1 = service.login("alice", "p1")
        t2 = service.login("bob", "p2")
        assert t1 != t2

    def test_token_resolves_correct_user(self, service):
        service.register("alice", "pwd")
        token = service.login("alice", "pwd")
        user = service.get_by_token(token)
        assert user.username == "alice"

    def test_wrong_password_returns_none(self, service):
        service.register("alice", "pwd")
        assert service.login("alice", "wrong") is None

    def test_unknown_user_returns_none(self, service):
        assert service.login("ghost", "pwd") is None

    def test_multiple_logins_same_user(self, service):
        service.register("alice", "pwd")
        t1 = service.login("alice", "pwd")
        t2 = service.login("alice", "pwd")
        assert t1 == t2  # same token for same user


class TestMultiUserAccess:
    def test_admin_can_call_admin_endpoint(self):
        admin = make_test_user(role="admin")
        require_minimum_role(admin, "admin")  # no raise

    def test_user_cannot_call_admin_endpoint(self):
        user = make_test_user(role="user")
        with pytest.raises(HTTPException) as exc:
            require_minimum_role(user, "admin")
        assert exc.value.status_code == 403

    def test_admin_can_call_user_endpoint(self):
        admin = make_test_user(role="admin")
        require_minimum_role(admin, "user")  # no raise

    def test_user_can_call_user_endpoint(self):
        user = make_test_user(role="user")
        require_minimum_role(user, "user")  # no raise

    def test_guest_can_call_guest_endpoint(self):
        guest = make_test_user(role="guest")
        require_minimum_role(guest, "guest")  # no raise

    def test_get_user_by_id(self, service):
        user = service.register("alice", "pwd")
        found = service.get_by_id(user.user_id)
        assert found is not None
        assert found.username == "alice"

    def test_get_user_permissions_admin(self, service):
        user = service.register("admin1", "pwd", "admin")
        perms = service.get_user_permissions(user.user_id)
        assert "device:delete" in perms
        assert "user:write" in perms

    def test_get_user_permissions_guest(self, service):
        user = service.register("guest1", "pwd", "guest")
        perms = service.get_user_permissions(user.user_id)
        assert perms == ["device:read"]
