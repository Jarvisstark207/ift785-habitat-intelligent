"""Tests unitaires - Pattern Facade (DashboardFacade)"""

import pytest

from domain.dashboard.dashboard_facade import DashboardFacade
from domain.integrations.smart_home_adapter import PhilipsHueAdapter, NestAdapter


@pytest.fixture
def facade():
    return DashboardFacade()


@pytest.fixture
def facade_avec_adapters():
    f = DashboardFacade()
    f.register_adapter(PhilipsHueAdapter())
    f.register_adapter(NestAdapter())
    return f


class TestDashboardFacadeBase:

    def test_facade_instantiation(self, facade):
        """DashboardFacade peut etre instanciee sans parametres"""
        assert facade is not None

    def test_get_summary_retourne_dict(self, facade):
        summary = facade.get_summary()
        assert isinstance(summary, dict)

    def test_get_summary_cles_requises(self, facade):
        summary = facade.get_summary()
        assert "house_mode" in summary
        assert "active_profile" in summary
        assert "alerts" in summary
        assert "scenarios" in summary
        assert "integrations" in summary

    def test_get_widgets_retourne_liste(self, facade):
        widgets = facade.get_widgets()
        assert isinstance(widgets, list)

    def test_get_widgets_contient_4_widgets(self, facade):
        widgets = facade.get_widgets()
        assert len(widgets) == 4

    def test_get_widgets_structure(self, facade):
        widget = facade.get_widgets()[0]
        assert "id" in widget
        assert "title" in widget
        assert "type" in widget
        assert "data" in widget


class TestDashboardFacadeAdapters:

    def test_register_adapter(self, facade):
        """On peut enregistrer un adapter dans la facade"""
        facade.register_adapter(PhilipsHueAdapter())
        summary = facade.get_summary()
        assert len(summary["integrations"]) == 1

    def test_register_multiple_adapters(self, facade_avec_adapters):
        summary = facade_avec_adapters.get_summary()
        assert len(summary["integrations"]) == 2

    def test_integrations_contiennent_status(self, facade_avec_adapters):
        summary = facade_avec_adapters.get_summary()
        for integration in summary["integrations"]:
            assert "name" in integration
            assert "status" in integration

    def test_sans_adapter_integrations_vides(self, facade):
        summary = facade.get_summary()
        assert summary["integrations"] == []


class TestDashboardFacadeAvecServices:

    def test_summary_mode_maison_sans_house(self, facade):
        """Sans house service, le mode est 'inconnu'"""
        assert facade.get_summary()["house_mode"] == "inconnu"

    def test_summary_profil_sans_profiles(self, facade):
        """Sans profile manager, le profil actif est None"""
        profile_data = facade.get_summary()["active_profile"]
        assert profile_data["name"] is None

    def test_summary_scenarios_sans_manager(self, facade):
        """Sans scenario manager, le compte est 0"""
        scenarios = facade.get_summary()["scenarios"]
        assert scenarios["total"] == 0
        assert scenarios["active"] == 0

    def test_facade_avec_house(self):
        """Facade avec un House retourne le bon mode"""
        from domain.house_states.house import House
        house = House()
        f = DashboardFacade(house=house)
        assert f.get_summary()["house_mode"] == "domicile"

    def test_facade_avec_profile_manager(self):
        """Facade avec ProfileManager retourne le bon profil"""
        from domain.profiles.profile_manager import ProfileManager
        pm = ProfileManager()
        profiles = pm.get_all_profiles()
        pm.activate_profile(profiles[0].id)
        f = DashboardFacade(profile_manager=pm)
        profile_data = f.get_summary()["active_profile"]
        assert profile_data["name"] is not None
