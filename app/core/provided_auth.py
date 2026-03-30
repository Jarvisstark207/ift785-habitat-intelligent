"""
provided_auth.py
================
Module d'authentification fourni pour l'iteration 7.

NE PAS MODIFIER ce fichier.
Il fournit une couche d'authentification minimale (tokens statiques)
pour que @require_role soit fonctionnel sans infrastructure JWT complète.

Tokens de test disponibles :
  - "token_admin"  -> User(id="admin_user",  role="admin")
  - "token_user"   -> User(id="regular_user", role="user")
  - "token_guest"  -> User(id="guest_user",   role="guest")
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional

from fastapi import HTTPException, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi import Depends


# ---------------------------------------------------------------------------
# Modele utilisateur
# ---------------------------------------------------------------------------

@dataclass
class User:
    """Representation minimale d'un utilisateur authentifie."""
    id: str
    role: str
    is_authenticated: bool = True
    permissions: list = field(default_factory=list)

    def has_role(self, required_role: str) -> bool:
        """Verifie si l'utilisateur possede le role requis (hierarchie incluse)."""
        return ROLE_HIERARCHY.get(self.role, 0) >= ROLE_HIERARCHY.get(required_role, 0)


# ---------------------------------------------------------------------------
# Hierarchie des roles  (admin > user > guest)
# ---------------------------------------------------------------------------

ROLE_HIERARCHY: dict[str, int] = {
    "admin": 3,
    "user":  2,
    "guest": 1,
}

ROLES = set(ROLE_HIERARCHY.keys())


# ---------------------------------------------------------------------------
# Base de tokens statiques (remplace la verification JWT)
# ---------------------------------------------------------------------------

_TOKEN_DB: dict[str, User] = {
    "token_admin": User(
        id="admin_user",
        role="admin",
        permissions=["device:read", "device:write", "device:delete", "user:read", "user:write"],
    ),
    "token_user": User(
        id="regular_user",
        role="user",
        permissions=["device:read", "device:write"],
    ),
    "token_guest": User(
        id="guest_user",
        role="guest",
        permissions=["device:read"],
    ),
}


# ---------------------------------------------------------------------------
# Resolution de l'utilisateur courant
# ---------------------------------------------------------------------------

_security = HTTPBearer(auto_error=False)


def get_current_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(_security),
) -> User:
    """
    Resout l'utilisateur depuis le token Bearer.
    Leve HTTPException(401) si le token est absent ou invalide.
    """
    if credentials is None:
        raise HTTPException(
            status_code=401,
            detail="Token d'authentification manquant (header Authorization: Bearer <token>)",
        )

    user = _TOKEN_DB.get(credentials.credentials)
    if user is None:
        raise HTTPException(
            status_code=401,
            detail=f"Token invalide : '{credentials.credentials}' non reconnu",
        )

    return user


def get_current_user_from_request(request: Request) -> Optional[User]:
    """
    Variante sans Depends - utile dans les decorateurs qui recoivent request.
    Retourne None si le token est absent ou invalide (ne leve pas d'exception).
    """
    auth_header = request.headers.get("Authorization", "")
    if not auth_header.startswith("Bearer "):
        return None
    token = auth_header[len("Bearer "):]
    return _TOKEN_DB.get(token)


# ---------------------------------------------------------------------------
# Verification de role utilitaire
# ---------------------------------------------------------------------------

def require_minimum_role(user: User, required_role: str) -> None:
    """
    Verifie que l'utilisateur possede le role minimum requis.
    Leve HTTPException(403) si non autorise.
    """
    if required_role not in ROLE_HIERARCHY:
        raise ValueError(f"Role inconnu : '{required_role}'. Valeurs : {ROLES}")

    if not user.has_role(required_role):
        raise HTTPException(
            status_code=403,
            detail=(
                f"Acces refuse : role '{user.role}' insuffisant "
                f"(requis : '{required_role}' ou superieur)"
            ),
        )


# ---------------------------------------------------------------------------
# Helpers pour les tests
# ---------------------------------------------------------------------------

def make_test_user(role: str = "user", user_id: str = "test_user") -> User:
    """
    Cree un utilisateur de test sans passer par les tokens statiques.
    """
    if role not in ROLE_HIERARCHY:
        raise ValueError(f"Role inconnu : '{role}'. Valeurs : {ROLES}")
    return User(id=user_id, role=role)
