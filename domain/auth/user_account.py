"""Modele de compte utilisateur - Iteration 7"""

import hashlib
import uuid
from dataclasses import dataclass, field
from typing import List

_ROLE_PERMISSIONS = {
    "admin": ["device:read", "device:write", "device:delete", "user:read", "user:write"],
    "user": ["device:read", "device:write"],
    "guest": ["device:read"],
}


@dataclass
class UserAccount:
    """Compte utilisateur persiste dans le systeme."""
    user_id: str
    username: str
    password_hash: str
    role: str = "user"
    token: str = ""
    permissions: List[str] = field(default_factory=list)

    @staticmethod
    def hash_password(password: str) -> str:
        """Hache un mot de passe avec SHA-256."""
        return hashlib.sha256(password.encode()).hexdigest()

    def check_password(self, password: str) -> bool:
        """Verifie un mot de passe en clair contre le hash stocke."""
        return self.password_hash == self.hash_password(password)

    def to_dict(self) -> dict:
        return {
            "user_id": self.user_id,
            "username": self.username,
            "role": self.role,
            "permissions": self.permissions,
        }


def create_user_account(username: str, password: str, role: str = "user") -> UserAccount:
    """Fabrique un UserAccount avec hash et permissions par defaut."""
    return UserAccount(
        user_id=str(uuid.uuid4()),
        username=username,
        password_hash=UserAccount.hash_password(password),
        role=role,
        permissions=_ROLE_PERMISSIONS.get(role, []),
    )
