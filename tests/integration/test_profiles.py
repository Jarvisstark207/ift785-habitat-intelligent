"""Tests d'integration - Profils utilisateurs (Strategy)"""

import pytest

from domain.profiles.profile_manager import ProfileManager
from domain.profiles.profile import UserProfile
from domain.patterns.strategy import (
    EconomyStrategy,
    ComfortStrategy,
    AbsenceStrategy,
)


@pytest.fixture
def manager():
    return ProfileManager()


class TestProfilesCRUD:

    def test_profils_defaut_initialises(self, manager):
        """Trois profils par defaut sont crees a l'initialisation"""
        profiles = manager.get_all_profiles()
        assert len(profiles) == 3

    def test_profils_defaut_types_corrects(self, manager):
        """Les profils par defaut ont les bons types de strategies"""
        types = {p.strategy_type for p in manager.get_all_profiles()}
        assert "economy" in types
        assert "comfort" in types
        assert "absence" in types

    def test_creation_profil_personnalise(self, manager):
        """Un profil personnalise peut etre cree"""
        profile = manager.create_profile(
            name="Mon profil",
            strategy_type="comfort",
            settings={"custom_temp": 22.0},
        )
        assert isinstance(profile, UserProfile)
        assert profile.name == "Mon profil"
        assert profile.strategy_type == "comfort"

    def test_profil_personnalise_dans_liste(self, manager):
        """Un profil cree apparait dans la liste"""
        manager.create_profile(name="Nouveau", strategy_type="economy")
        profiles = manager.get_all_profiles()
        assert len(profiles) == 4

    def test_type_strategie_invalide_leve_erreur(self, manager):
        """Creer un profil avec un type invalide leve une erreur"""
        with pytest.raises(ValueError):
            manager.create_profile(name="Invalide", strategy_type="unknown")

    def test_suppression_profil(self, manager):
        """Un profil peut etre supprime"""
        profile = manager.create_profile(name="A supprimer", strategy_type="economy")
        result = manager.delete_profile(profile.id)
        assert result is True
        assert manager.get_profile(profile.id) is None


class TestProfilesActivation:

    def test_activation_profil_economy(self, manager):
        """Activer un profil economie retourne True et applique la strategie"""
        profiles = manager.get_all_profiles()
        economy = next(p for p in profiles if p.strategy_type == "economy")
        result = manager.activate_profile(economy.id)
        assert result is True
        assert manager.get_current_strategy() is not None

    def test_profil_actif_est_marque(self, manager):
        """Le profil actif a is_active=True"""
        profiles = manager.get_all_profiles()
        comfort = next(p for p in profiles if p.strategy_type == "comfort")
        manager.activate_profile(comfort.id)
        assert comfort.is_active is True

    def test_un_seul_profil_actif_a_la_fois(self, manager):
        """Un seul profil est actif a la fois"""
        profiles = manager.get_all_profiles()
        economy = next(p for p in profiles if p.strategy_type == "economy")
        comfort = next(p for p in profiles if p.strategy_type == "comfort")

        manager.activate_profile(economy.id)
        manager.activate_profile(comfort.id)

        active_count = sum(1 for p in manager.get_all_profiles() if p.is_active)
        assert active_count == 1

    def test_strategie_economy_appliquee(self, manager):
        """Activer le profil economie applique EconomyStrategy"""
        profiles = manager.get_all_profiles()
        economy = next(p for p in profiles if p.strategy_type == "economy")
        manager.activate_profile(economy.id)
        strategy = manager.get_current_strategy()
        assert isinstance(strategy, EconomyStrategy)

    def test_strategie_comfort_appliquee(self, manager):
        """Activer le profil confort applique ComfortStrategy"""
        profiles = manager.get_all_profiles()
        comfort = next(p for p in profiles if p.strategy_type == "comfort")
        manager.activate_profile(comfort.id)
        assert isinstance(manager.get_current_strategy(), ComfortStrategy)

    def test_strategie_absence_appliquee(self, manager):
        """Activer le profil absence applique AbsenceStrategy"""
        profiles = manager.get_all_profiles()
        absence = next(p for p in profiles if p.strategy_type == "absence")
        manager.activate_profile(absence.id)
        assert isinstance(manager.get_current_strategy(), AbsenceStrategy)

    def test_get_current_profile_sans_activation(self, manager):
        """Sans profil actif, get_current_profile retourne None"""
        assert manager.get_current_profile() is None

    def test_get_current_profile_apres_activation(self, manager):
        """Apres activation, get_current_profile retourne le bon profil"""
        profiles = manager.get_all_profiles()
        economy = next(p for p in profiles if p.strategy_type == "economy")
        manager.activate_profile(economy.id)
        current = manager.get_current_profile()
        assert current is not None
        assert current.id == economy.id

    def test_profil_inexistant_retourne_false(self, manager):
        """Activer un profil inexistant retourne False"""
        result = manager.activate_profile("id-inexistant")
        assert result is False

    def test_strategie_fournit_temperature_cible(self, manager):
        """La strategie courante fournit une temperature cible"""
        profiles = manager.get_all_profiles()
        economy = next(p for p in profiles if p.strategy_type == "economy")
        manager.activate_profile(economy.id)
        temp = manager.get_current_strategy().get_target_temperature()
        assert temp == 19.0
