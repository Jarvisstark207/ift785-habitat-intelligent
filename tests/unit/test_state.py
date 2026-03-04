"""Tests unitaires - Pattern State"""

import pytest

from domain.house_states.house import House
from domain.house_states.states import (
    DomicileState,
    NuitState,
    AbsenceState,
    VacancesState,
    get_state_for_mode,
)
from domain.patterns.state import HouseState


# ---------------------------------------------------------------------------
# Tests etats concrets
# ---------------------------------------------------------------------------

class TestDomicileState:

    def test_mode_name_domicile(self):
        """Le nom du mode est 'domicile'"""
        state = DomicileState()
        assert state.get_mode_name() == "domicile"

    def test_config_domicile_lumieres_100(self):
        """En mode domicile, les lumieres couloir sont a 100%"""
        state = DomicileState()
        config = state.get_mode_config()
        assert config["lights_corridor"] == 100

    def test_domicile_notifications_sonores_actives(self):
        """En mode domicile, les notifications sonores sont actives"""
        config = DomicileState().get_mode_config()
        assert config["sound_notifications"] is True

    def test_domicile_est_instance_house_state(self):
        """DomicileState est une instance de HouseState"""
        assert isinstance(DomicileState(), HouseState)


class TestNuitState:

    def test_mode_name_nuit(self):
        """Le nom du mode est 'nuit'"""
        assert NuitState().get_mode_name() == "nuit"

    def test_config_nuit_lumieres_10(self):
        """En mode nuit, les lumieres couloir sont a 10%"""
        config = NuitState().get_mode_config()
        assert config["lights_corridor"] == 10

    def test_nuit_pas_de_notifications_sonores(self):
        """En mode nuit, les notifications sonores sont desactivees"""
        config = NuitState().get_mode_config()
        assert config["sound_notifications"] is False

    def test_nuit_alertes_mouvements_actives(self):
        """En mode nuit, les alertes mouvement sont actives"""
        config = NuitState().get_mode_config()
        assert config["motion_alerts"] is True


class TestAbsenceState:

    def test_mode_name_absence(self):
        """Le nom du mode est 'absence'"""
        assert AbsenceState().get_mode_name() == "absence"

    def test_absence_securite_maximale(self):
        """En mode absence, la securite est au maximum"""
        config = AbsenceState().get_mode_config()
        assert config["security_max"] is True

    def test_absence_lumieres_eteintes(self):
        """En mode absence, les lumieres sont eteintes"""
        config = AbsenceState().get_mode_config()
        assert config["lights_corridor"] == 0


class TestVacancesState:

    def test_mode_name_vacances(self):
        """Le nom du mode est 'vacances'"""
        assert VacancesState().get_mode_name() == "vacances"

    def test_vacances_simulation_presence(self):
        """En mode vacances, la simulation de presence est activee"""
        config = VacancesState().get_mode_config()
        assert config.get("presence_simulation") is True

    def test_vacances_cameras_actives(self):
        """En mode vacances, les cameras sont actives"""
        config = VacancesState().get_mode_config()
        assert config.get("cameras_active") is True


# ---------------------------------------------------------------------------
# Tests House (contexte State)
# ---------------------------------------------------------------------------

class TestHouse:

    @pytest.fixture
    def house(self):
        return House()

    def test_mode_initial_domicile(self, house):
        """La maison demarre en mode domicile"""
        assert house.get_current_mode() == "domicile"

    def test_changement_mode_manuel(self, house):
        """Le mode change correctement lors d'un set_state"""
        house.set_state(NuitState())
        assert house.get_current_mode() == "nuit"

    def test_historique_enregistre_transitions(self, house):
        """L'historique enregistre les transitions de mode"""
        house.set_state(NuitState())
        house.set_state(DomicileState())
        history = house.get_mode_history()
        assert len(history) == 2
        assert history[0]["from"] == "domicile"
        assert history[0]["to"] == "nuit"

    def test_presence_en_nuit_retourne_domicile(self, house):
        """La detection de presence en mode nuit bascule en domicile"""
        house.set_state(NuitState())
        house.handle_presence_detected()
        assert house.get_current_mode() == "domicile"

    def test_nuit_depuis_domicile(self, house):
        """Le passage au mode nuit depuis domicile fonctionne"""
        house.handle_night_time()
        assert house.get_current_mode() == "nuit"

    def test_presence_en_absence_retourne_domicile(self, house):
        """La detection de presence en absence bascule en domicile"""
        house.set_state(AbsenceState())
        house.handle_presence_detected()
        assert house.get_current_mode() == "domicile"

    def test_get_mode_config_retourne_dict(self, house):
        """get_mode_config retourne un dictionnaire non vide"""
        config = house.get_mode_config()
        assert isinstance(config, dict)
        assert len(config) > 0

    def test_log_event_enregistre(self, house):
        """log_event enregistre l'evenement dans le journal"""
        initial_count = len(house._event_log)
        house.log_event("test event")
        assert len(house._event_log) == initial_count + 1

    def test_vacances_presence_leve_alerte(self, house):
        """En mode vacances, une presence detectee genere une alerte"""
        house.set_state(VacancesState())
        initial_log_count = len(house._event_log)
        house.handle_presence_detected()
        assert len(house._event_log) > initial_log_count
        assert house.get_current_mode() == "vacances"  # reste en vacances


# ---------------------------------------------------------------------------
# Tests get_state_for_mode
# ---------------------------------------------------------------------------

class TestGetStateForMode:

    def test_get_domicile(self):
        """get_state_for_mode retourne DomicileState"""
        state = get_state_for_mode("domicile")
        assert isinstance(state, DomicileState)

    def test_get_nuit(self):
        """get_state_for_mode retourne NuitState"""
        state = get_state_for_mode("nuit")
        assert isinstance(state, NuitState)

    def test_get_absence(self):
        """get_state_for_mode retourne AbsenceState"""
        state = get_state_for_mode("absence")
        assert isinstance(state, AbsenceState)

    def test_get_vacances(self):
        """get_state_for_mode retourne VacancesState"""
        state = get_state_for_mode("vacances")
        assert isinstance(state, VacancesState)

    def test_mode_inconnu_leve_erreur(self):
        """get_state_for_mode leve ValueError pour un mode inconnu"""
        with pytest.raises(ValueError):
            get_state_for_mode("mode_inexistant")
