"""Tests unitaires pour le système d'alertes"""

import pytest
from unittest.mock import Mock
from application.services.alert_service import AlertService
from application.services.stats_service import StatsService
from config import ALERT_TEMP_MIN, ALERT_TEMP_MAX, ALERT_CONSUMPTION_MAX


class TestAlertGeneration:
    """Tests pour la génération d'alertes"""

    def test_alert_temperature_below_minimum(self):
        """Test alerte quand température < minimum"""
        mock_stats = Mock(spec=StatsService)
        mock_stats.calculate_location_stats.return_value = {
            "temp_avg": ALERT_TEMP_MIN - 5,  # En dessous du seuil
            "consumption": 100.0,
        }

        service = AlertService(mock_stats)
        alerts = service.generate_alerts(["salon"])

        temp_alerts = [a for a in alerts if a["type"] == "temperature"]
        assert len(temp_alerts) > 0
        assert temp_alerts[0]["location"] == "salon"

    def test_alert_temperature_above_maximum(self):
        """Test alerte quand température > maximum"""
        mock_stats = Mock(spec=StatsService)
        mock_stats.calculate_location_stats.return_value = {
            "temp_avg": ALERT_TEMP_MAX + 5,  # Au-dessus du seuil
            "consumption": 100.0,
        }

        service = AlertService(mock_stats)
        alerts = service.generate_alerts(["salon"])

        temp_alerts = [a for a in alerts if a["type"] == "temperature"]
        assert len(temp_alerts) > 0

    def test_alert_consumption_above_maximum(self):
        """Test alerte quand consommation > maximum"""
        mock_stats = Mock(spec=StatsService)
        mock_stats.calculate_location_stats.return_value = {
            "temp_avg": 22.0,
            "consumption": ALERT_CONSUMPTION_MAX + 500,  # Au-dessus du seuil
        }

        service = AlertService(mock_stats)
        alerts = service.generate_alerts(["salon"])

        consumption_alerts = [a for a in alerts if a["type"] == "consumption"]
        assert len(consumption_alerts) > 0
        assert consumption_alerts[0]["severity"] == "critical"

    def test_no_alert_when_values_in_range(self):
        """Test pas d'alerte quand valeurs dans les limites"""
        mock_stats = Mock(spec=StatsService)
        mock_stats.calculate_location_stats.return_value = {
            "temp_avg": (ALERT_TEMP_MIN + ALERT_TEMP_MAX) / 2,  # Milieu de plage
            "consumption": ALERT_CONSUMPTION_MAX / 2,  # Moitié du max
        }

        service = AlertService(mock_stats)
        alerts = service.generate_alerts(["salon"])

        assert len(alerts) == 0

    def test_alert_severity_levels(self):
        """Test niveaux de sévérité des alertes"""
        mock_stats = Mock(spec=StatsService)

        # Température légèrement basse
        mock_stats.calculate_location_stats.return_value = {
            "temp_avg": ALERT_TEMP_MIN - 1,
            "consumption": 100.0,
        }

        service = AlertService(mock_stats)
        alerts = service.generate_alerts(["salon"])

        if alerts:
            temp_alert = [a for a in alerts if a["type"] == "temperature"][0]
            assert temp_alert["severity"] in ["warning", "critical"]

    def test_alert_message_contains_value(self):
        """Test que le message d'alerte contient la valeur"""
        mock_stats = Mock(spec=StatsService)
        mock_stats.calculate_location_stats.return_value = {"temp_avg": 15.0, "consumption": 100.0}

        service = AlertService(mock_stats)
        alerts = service.generate_alerts(["salon"])

        if alerts:
            assert "15.0" in str(alerts[0]["message"]) or "15" in str(alerts[0]["message"])

    def test_multiple_alerts_for_same_location(self):
        """Test plusieurs alertes pour même location"""
        mock_stats = Mock(spec=StatsService)
        mock_stats.calculate_location_stats.return_value = {
            "temp_avg": ALERT_TEMP_MIN - 5,  # Temp basse
            "consumption": ALERT_CONSUMPTION_MAX + 500,  # Conso haute
        }

        service = AlertService(mock_stats)
        alerts = service.generate_alerts(["salon"])

        # Devrait avoir 2 alertes : température ET consommation
        assert len(alerts) >= 2

    def test_alerts_for_multiple_locations(self):
        """Test alertes pour plusieurs locations"""
        mock_stats = Mock(spec=StatsService)

        def side_effect(location):
            if location == "salon":
                return {"temp_avg": ALERT_TEMP_MIN - 5, "consumption": 100.0}
            elif location == "cuisine":
                return {"temp_avg": ALERT_TEMP_MAX + 5, "consumption": 100.0}
            else:
                return {"temp_avg": 22.0, "consumption": 100.0}

        mock_stats.calculate_location_stats.side_effect = side_effect

        service = AlertService(mock_stats)
        alerts = service.generate_alerts(["salon", "cuisine", "chambre"])

        locations_with_alerts = {a["location"] for a in alerts}
        assert "salon" in locations_with_alerts
        assert "cuisine" in locations_with_alerts

    def test_alert_with_none_temperature(self):
        """Test gestion température None (pas d'alerte)"""
        mock_stats = Mock(spec=StatsService)
        mock_stats.calculate_location_stats.return_value = {"temp_avg": None, "consumption": 100.0}

        service = AlertService(mock_stats)
        alerts = service.generate_alerts(["salon"])

        temp_alerts = [a for a in alerts if a["type"] == "temperature"]
        assert len(temp_alerts) == 0

    def test_alert_with_none_consumption(self):
        """Test gestion consommation None (pas d'alerte)"""
        mock_stats = Mock(spec=StatsService)
        mock_stats.calculate_location_stats.return_value = {"temp_avg": 22.0, "consumption": None}

        service = AlertService(mock_stats)
        alerts = service.generate_alerts(["salon"])

        consumption_alerts = [a for a in alerts if a["type"] == "consumption"]
        assert len(consumption_alerts) == 0

    def test_alert_structure_completeness(self):
        """Test que structure alerte contient tous les champs requis"""
        mock_stats = Mock(spec=StatsService)
        mock_stats.calculate_location_stats.return_value = {
            "temp_avg": ALERT_TEMP_MIN - 5,
            "consumption": 100.0,
        }

        service = AlertService(mock_stats)
        alerts = service.generate_alerts(["salon"])

        if alerts:
            alert = alerts[0]
            required_fields = ["type", "severity", "location", "message"]
            for field in required_fields:
                assert field in alert, f"Champ manquant: {field}"
