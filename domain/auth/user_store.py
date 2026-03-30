"""Stockage en memoire des comptes utilisateurs - Singleton - Iteration 7"""

from typing import Dict, List, Optional
from domain.auth.user_account import UserAccount, create_user_account

VALID_ROLES = {"admin", "user", "guest"}


class UserStore:
    """Stockage singleton des comptes utilisateurs (isolation memoire)."""

    _instance: Optional["UserStore"] = None

    def __init__(self):
        self._users: Dict[str, UserAccount] = {}   # username -> UserAccount
        self._tokens: Dict[str, str] = {}           # token -> username

    @classmethod
    def get_instance(cls) -> "UserStore":
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    @classmethod
    def reset(cls) -> None:
        """Reinitialise le singleton (pour les tests)."""
        cls._instance = None

    def register(self, username: str, password: str, role: str = "user") -> UserAccount:
        """Enregistre un nouvel utilisateur."""
        if username in self._users:
            raise ValueError(f"Utilisateur '{username}' deja enregistre")
        if role not in VALID_ROLES:
            raise ValueError(f"Role inconnu : '{role}'")
        user = create_user_account(username, password, role)
        self._users[username] = user
        return user

    def login(self, username: str, password: str) -> Optional[str]:
        """Authentifie un utilisateur. Retourne un token ou None."""
        user = self._users.get(username)
        if user is None or not user.check_password(password):
            return None
        token = f"token_{user.user_id}"
        self._tokens[token] = username
        user.token = token
        return token

    def get_by_token(self, token: str) -> Optional[UserAccount]:
        username = self._tokens.get(token)
        if username is None:
            return None
        return self._users.get(username)

    def get_by_id(self, user_id: str) -> Optional[UserAccount]:
        for user in self._users.values():
            if user.user_id == user_id:
                return user
        return None

    def get_all(self) -> List[UserAccount]:
        return list(self._users.values())

    def clear(self) -> None:
        self._users.clear()
        self._tokens.clear()
