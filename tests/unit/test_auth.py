"""Tests unitaires pour le module d'authentification - Iteration 7"""

import pytest
from domain.auth.user_account import UserAccount, create_user_account
from domain.auth.user_store import UserStore
from application.services.auth_service import AuthService
from app.core.provided_auth import make_test_user, ROLE_HIERARCHY, User


@pytest.fixture(autouse=True)
def reset_store():
    UserStore.reset()
    yield
    UserStore.reset()


@pytest.fixture
def store():
    return UserStore.get_instance()


@pytest.fixture
def auth_service(store):
    return AuthService(store)


class TestUserAccount:
    def test_hash_password_is_deterministic(self):
        h1 = UserAccount.hash_password("secret")
        h2 = UserAccount.hash_password("secret")
        assert h1 == h2

    def test_hash_password_differs_for_different_passwords(self):
        assert UserAccount.hash_password("abc") != UserAccount.hash_password("xyz")

    def test_check_password_correct(self):
        user = create_user_account("alice", "pass123")
        assert user.check_password("pass123") is True

    def test_check_password_wrong(self):
        user = create_user_account("alice", "pass123")
        assert user.check_password("wrong") is False

    def test_to_dict_contains_required_keys(self):
        user = create_user_account("bob", "pwd", "admin")
        d = user.to_dict()
        assert "user_id" in d
        assert "username" in d
        assert "role" in d
        assert "permissions" in d

    def test_create_user_account_sets_role(self):
        user = create_user_account("alice", "pwd", "admin")
        assert user.role == "admin"

    def test_create_user_account_sets_permissions(self):
        user = create_user_account("alice", "pwd", "admin")
        assert "device:delete" in user.permissions

    def test_guest_permissions(self):
        user = create_user_account("guest1", "pwd", "guest")
        assert user.permissions == ["device:read"]


class TestUserStore:
    def test_register_new_user(self, store):
        user = store.register("alice", "pass")
        assert user.username == "alice"

    def test_register_duplicate_raises(self, store):
        store.register("alice", "pass")
        with pytest.raises(ValueError, match="deja enregistre"):
            store.register("alice", "other")

    def test_register_invalid_role_raises(self, store):
        with pytest.raises(ValueError, match="Role inconnu"):
            store.register("alice", "pass", role="superadmin")

    def test_login_valid_returns_token(self, store):
        store.register("alice", "pass")
        token = store.login("alice", "pass")
        assert token is not None
        assert isinstance(token, str)

    def test_login_wrong_password_returns_none(self, store):
        store.register("alice", "pass")
        assert store.login("alice", "wrong") is None

    def test_login_unknown_user_returns_none(self, store):
        assert store.login("nobody", "pass") is None

    def test_get_by_token(self, store):
        store.register("alice", "pass")
        token = store.login("alice", "pass")
        user = store.get_by_token(token)
        assert user is not None
        assert user.username == "alice"

    def test_get_by_token_invalid_returns_none(self, store):
        assert store.get_by_token("invalid_token") is None

    def test_get_by_id(self, store):
        created = store.register("alice", "pass")
        found = store.get_by_id(created.user_id)
        assert found is not None
        assert found.username == "alice"

    def test_get_by_id_unknown_returns_none(self, store):
        assert store.get_by_id("nonexistent-id") is None

    def test_get_all_returns_registered_users(self, store):
        store.register("alice", "pass")
        store.register("bob", "pass")
        users = store.get_all()
        assert len(users) == 2

    def test_clear_empties_store(self, store):
        store.register("alice", "pass")
        store.clear()
        assert store.get_all() == []


class TestAuthService:
    def test_register_via_service(self, auth_service):
        user = auth_service.register("charlie", "pwd")
        assert user.username == "charlie"

    def test_login_via_service(self, auth_service):
        auth_service.register("charlie", "pwd")
        token = auth_service.login("charlie", "pwd")
        assert token is not None

    def test_get_user_permissions(self, auth_service):
        user = auth_service.register("admin1", "pwd", "admin")
        perms = auth_service.get_user_permissions(user.user_id)
        assert "device:delete" in perms

    def test_get_all_users(self, auth_service):
        auth_service.register("u1", "p")
        auth_service.register("u2", "p")
        assert len(auth_service.get_all_users()) == 2


class TestProvidedAuthHelpers:
    def test_make_test_user_default_role(self):
        user = make_test_user()
        assert user.role == "user"

    def test_make_test_user_admin(self):
        user = make_test_user(role="admin")
        assert user.role == "admin"

    def test_make_test_user_invalid_role_raises(self):
        with pytest.raises(ValueError):
            make_test_user(role="superadmin")

    def test_role_hierarchy_admin_highest(self):
        assert ROLE_HIERARCHY["admin"] > ROLE_HIERARCHY["user"]
        assert ROLE_HIERARCHY["user"] > ROLE_HIERARCHY["guest"]

    def test_user_has_role_same_role(self):
        user = User(id="u1", role="user")
        assert user.has_role("user") is True

    def test_user_has_role_higher(self):
        user = User(id="u1", role="admin")
        assert user.has_role("user") is True

    def test_user_has_role_insufficient(self):
        user = User(id="u1", role="guest")
        assert user.has_role("admin") is False
