"""Service d'authentification et de gestion des utilisateurs - Iteration 7"""

from typing import List, Optional
from domain.auth.user_account import UserAccount
from domain.auth.user_store import UserStore


class AuthService:
    """Service d'authentification : register, login, gestion des utilisateurs."""

    def __init__(self, user_store: UserStore = None):
        self._store = user_store or UserStore.get_instance()

    def register(self, username: str, password: str, role: str = "user") -> UserAccount:
        """Enregistre un nouvel utilisateur."""
        return self._store.register(username, password, role)

    def login(self, username: str, password: str) -> Optional[str]:
        """Authentifie un utilisateur et retourne un token."""
        return self._store.login(username, password)

    def get_by_token(self, token: str) -> Optional[UserAccount]:
        """Retourne l'utilisateur associe au token."""
        return self._store.get_by_token(token)

    def get_by_id(self, user_id: str) -> Optional[UserAccount]:
        """Retourne un utilisateur par son identifiant."""
        return self._store.get_by_id(user_id)

    def get_all_users(self) -> List[UserAccount]:
        """Retourne tous les utilisateurs enregistres."""
        return self._store.get_all()

    def get_user_permissions(self, user_id: str) -> List[str]:
        """Retourne les permissions d'un utilisateur."""
        user = self._store.get_by_id(user_id)
        if user is None:
            return []
        return user.permissions
