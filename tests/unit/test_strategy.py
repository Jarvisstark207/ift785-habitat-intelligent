"""Tests unitaires - Pattern Strategy"""

import pytest

from domain.patterns.strategy import (
    EconomyStrategy,
    ComfortStrategy,
    AbsenceStrategy,
    HomeControlStrategy,
    get_strategy,
    STRATEGY_MAP,
)
from domain.profiles.profile_manager import ProfileManager


# ---------------------------------------------------------------------------
# Tests EconomyStrategy
# ---------------------------------------------------------------------------

class TestEconomyStrategy:

    @pytest.fixture
    def strategy(self):
        return EconomyStrategy()

    def test_temperature_cible_economie(self, strategy):
        """La strategie economie cible 19 degres"""
        assert strategy.get_target_temperature() == 19.0

    def test_nom_strategie_economie(self, strategy):
        """Le nom de la strategie est 'economy'"""
        assert strategy.get_strategy_name() == "economy"

    def test_lumieres_extinction_rapide(self, strategy):
        """Les lumieres s'eteignent apres 5 minutes d'inactivite"""
        behavior = strategy.get_light_behavior()
        assert behavior["auto_off_minutes"] == 5

    def test_seuils_alertes_economie(self, strategy):
        """Les seuils sont adaptes a la strategie economie"""
        thresholds = strategy.get_alert_thresholds()
        assert thresholds["consumption_max"] == 1500.0

    def test_apply_retourne_configuration_complete(self, strategy):
        """apply() retourne la configuration complete"""
        config = strategy.apply()
        assert "strategy" in config
        assert "target_temperature" in config
        assert "light_behavior" in config
        assert "alert_thresholds" in config
        assert config["strategy"] == "economy"


# ---------------------------------------------------------------------------
# Tests ComfortStrategy
# ---------------------------------------------------------------------------

class TestComfortStrategy:

    @pytest.fixture
    def strategy(self):
        return ComfortStrategy()

    def test_temperature_cible_confort(self, strategy):
        """La strategie confort cible 21 degres"""
        assert strategy.get_target_temperature() == 21.0

    def test_nom_strategie_confort(self, strategy):
        """Le nom de la strategie est 'comfort'"""
        assert strategy.get_strategy_name() == "comfort"

    def test_lumieres_confort_luminosite_max(self, strategy):
        """La strategie confort permet la luminosite maximale"""
        behavior = strategy.get_light_behavior()
        assert behavior["max_brightness"] == 100

    def test_seuils_alertes_confort(self, strategy):
        """Les seuils sont plus hauts en mode confort"""
        thresholds = strategy.get_alert_thresholds()
        assert thresholds["consumption_max"] == 2000.0


# ---------------------------------------------------------------------------
# Tests AbsenceStrategy
# ---------------------------------------------------------------------------

class TestAbsenceStrategy:

    @pytest.fixture
    def strategy(self):
        return AbsenceStrategy()

    def test_temperature_cible_absence(self, strategy):
        """La strategie absence cible 16 degres"""
        assert strategy.get_target_temperature() == 16.0

    def test_nom_strategie_absence(self, strategy):
        """Le nom de la strategie est 'absence'"""
        assert strategy.get_strategy_name() == "absence"

    def test_simulation_presence_activee(self, strategy):
        """La simulation de presence est activee"""
        behavior = strategy.get_light_behavior()
        assert behavior.get("presence_simulation") is True

    def test_securite_maximale(self, strategy):
        """La securite est au maximum en mode absence"""
        thresholds = strategy.get_alert_thresholds()
        assert thresholds.get("security_max") is True


# ---------------------------------------------------------------------------
# Tests get_strategy / STRATEGY_MAP
# ---------------------------------------------------------------------------

class TestGetStrategy:

    def test_get_strategy_economy(self):
        """get_strategy retourne une instance EconomyStrategy"""
        strategy = get_strategy("economy")
        assert isinstance(strategy, EconomyStrategy)

    def test_get_strategy_comfort(self):
        """get_strategy retourne une instance ComfortStrategy"""
        strategy = get_strategy("comfort")
        assert isinstance(strategy, ComfortStrategy)

    def test_get_strategy_absence(self):
        """get_strategy retourne une instance AbsenceStrategy"""
        strategy = get_strategy("absence")
        assert isinstance(strategy, AbsenceStrategy)

    def test_get_strategy_inconnu_leve_erreur(self):
        """get_strategy leve ValueError pour un type inconnu"""
        with pytest.raises(ValueError):
            get_strategy("unknown_strategy")

    def test_strategy_map_contient_tous_types(self):
        """STRATEGY_MAP contient les 3 types de strategies"""
        assert "economy" in STRATEGY_MAP
        assert "comfort" in STRATEGY_MAP
        assert "absence" in STRATEGY_MAP

    def test_strategies_implementent_interface(self):
        """Toutes les strategies implementent HomeControlStrategy"""
        for strategy_class in STRATEGY_MAP.values():
            assert issubclass(strategy_class, HomeControlStrategy)


# ---------------------------------------------------------------------------
# Tests ProfileManager (Strategy en contexte)
# ---------------------------------------------------------------------------

class TestProfileManagerStrategy:

    @pytest.fixture
    def manager(self):
        return ProfileManager()

    def test_changement_profil_change_strategie(self, manager):
        """Activer un profil change la strategie courante"""
        profiles = manager.get_all_profiles()
        economy_profile = next(
            p for p in profiles if p.strategy_type == "economy"
        )
        manager.activate_profile(economy_profile.id)
        strategy = manager.get_current_strategy()
        assert strategy is not None
        assert strategy.get_strategy_name() == "economy"

    def test_strategie_nulle_sans_profil_actif(self, manager):
        """Sans profil actif, la strategie est nulle"""
        assert manager.get_current_strategy() is None

    def test_changement_de_strategie_en_runtime(self, manager):
        """La strategie change bien a chaque activation de profil"""
        profiles = manager.get_all_profiles()
        economy = next(p for p in profiles if p.strategy_type == "economy")
        comfort = next(p for p in profiles if p.strategy_type == "comfort")

        manager.activate_profile(economy.id)
        assert manager.get_current_strategy().get_strategy_name() == "economy"

        manager.activate_profile(comfort.id)
        assert manager.get_current_strategy().get_strategy_name() == "comfort"
