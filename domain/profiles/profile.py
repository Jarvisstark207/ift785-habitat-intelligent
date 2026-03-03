"""Modele de profil utilisateur"""

from dataclasses import dataclass, field
from datetime import datetime
import uuid


@dataclass
class UserProfile:
    """Profil utilisateur avec strategie de controle associee"""

    name: str
    strategy_type: str  # economy, comfort, absence
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    is_active: bool = False
    settings: dict = field(default_factory=dict)
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "name": self.name,
            "strategy_type": self.strategy_type,
            "is_active": self.is_active,
            "settings": self.settings,
            "created_at": self.created_at,
        }
