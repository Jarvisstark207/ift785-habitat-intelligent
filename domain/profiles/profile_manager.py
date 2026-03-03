"""Gestionnaire de profils utilisateurs - utilise le pattern Strategy"""

from typing import Dict, List, Optional

from domain.patterns.strategy import HomeControlStrategy, get_strategy
from domain.profiles.profile import UserProfile


class ProfileManager:
    """Gestionnaire de profils.

    Applique le pattern Strategy: chaque profil est associe a une
    strategie de controle (Economy, Comfort, Absence).
    """

    def __init__(self) -> None:
        self._profiles: Dict[str, UserProfile] = {}
        self._active_profile_id: Optional[str] = None
        self._current_strategy: Optional[HomeControlStrategy] = None
        self._initialize_default_profiles()

    def _initialize_default_profiles(self) -> None:
        """Initialise les trois profils par defaut"""
        defaults = [
            UserProfile(
                name="Economie d'energie",
                strategy_type="economy",
                settings={"target_temp": 19.0, "auto_off_minutes": 5},
            ),
            UserProfile(
                name="Confort",
                strategy_type="comfort",
                settings={"target_temp": 21.0, "time_based_lights": True},
            ),
            UserProfile(
                name="Absence",
                strategy_type="absence",
                settings={"target_temp": 16.0, "presence_simulation": True},
            ),
        ]
        for profile in defaults:
            self._profiles[profile.id] = profile

    def create_profile(
        self,
        name: str,
        strategy_type: str,
        settings: Optional[dict] = None,
    ) -> UserProfile:
        """Cree un nouveau profil personnalise"""
        get_strategy(strategy_type)  # valide le type
        profile = UserProfile(
            name=name,
            strategy_type=strategy_type,
            settings=settings or {},
        )
        self._profiles[profile.id] = profile
        return profile

    def activate_profile(self, profile_id: str) -> bool:
        """Active un profil et change la strategie courante"""
        profile = self._profiles.get(profile_id)
        if not profile:
            return False
        if self._active_profile_id:
            old = self._profiles.get(self._active_profile_id)
            if old:
                old.is_active = False
        profile.is_active = True
        self._active_profile_id = profile_id
        self._current_strategy = get_strategy(profile.strategy_type)
        return True

    def get_current_profile(self) -> Optional[UserProfile]:
        """Retourne le profil actif"""
        if self._active_profile_id:
            return self._profiles.get(self._active_profile_id)
        return None

    def get_current_strategy(self) -> Optional[HomeControlStrategy]:
        """Retourne la strategie courante"""
        return self._current_strategy

    def get_all_profiles(self) -> List[UserProfile]:
        """Retourne tous les profils"""
        return list(self._profiles.values())

    def get_profile(self, profile_id: str) -> Optional[UserProfile]:
        """Retourne un profil par ID"""
        return self._profiles.get(profile_id)

    def delete_profile(self, profile_id: str) -> bool:
        """Supprime un profil"""
        if profile_id not in self._profiles:
            return False
        if self._active_profile_id == profile_id:
            self._active_profile_id = None
            self._current_strategy = None
        del self._profiles[profile_id]
        return True
