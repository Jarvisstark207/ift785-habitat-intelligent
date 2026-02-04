"""Tests unitaires pour AlertService"""

import pytest

from unittest.mock import Mock

from application.services.alert_service import AlertService

from application.services.stats_service import StatsService


class TestAlertService:
    """Tests pour le service d'alertes"""

    def test_generate_alerts_temperature_too_low(self):
        """Test alerte température trop basse"""

        mock_stats = Mock(spec=StatsService)

        mock_stats.calculate_location_stats.return_value = {
            "temp_avg": 15.0,  # Inférieur à ALERT_TEMP_MIN (18.0)
            "consumption": 100.0,
        }

        alert_service = AlertService(mock_stats)

        alerts = alert_service.generate_alerts(["salon"])

        assert len(alerts) > 0

        assert any(a["type"] == "temperature" for a in alerts)

        assert any("basse" in a["message"].lower() for a in alerts)

    def test_generate_alerts_temperature_too_high(self):
        """Test alerte température trop haute"""

        mock_stats = Mock(spec=StatsService)

        mock_stats.calculate_location_stats.return_value = {
            "temp_avg": 28.0,  # Supérieur à ALERT_TEMP_MAX (25.0)
            "consumption": 100.0,
        }

        alert_service = AlertService(mock_stats)

        alerts = alert_service.generate_alerts(["salon"])

        assert len(alerts) > 0

        assert any(a["type"] == "temperature" for a in alerts)

        assert any(
            "élevée" in a["message"].lower() or "haute" in a["message"].lower() for a in alerts
        )

    def test_generate_alerts_consumption_too_high(self):
        """Test alerte consommation excessive"""

        mock_stats = Mock(spec=StatsService)

        mock_stats.calculate_location_stats.return_value = {
            "temp_avg": 22.0,
            "consumption": 2500.0,  # Supérieur à ALERT_CONSUMPTION_MAX (2000.0)
        }

        alert_service = AlertService(mock_stats)

        alerts = alert_service.generate_alerts(["salon"])

        assert len(alerts) > 0

        assert any(a["type"] == "consumption" for a in alerts)

        assert any(a["severity"] == "critical" for a in alerts)

    def test_generate_no_alerts_when_values_normal(self):
        """Test pas d'alertes quand tout est normal"""

        mock_stats = Mock(spec=StatsService)

        mock_stats.calculate_location_stats.return_value = {
            "temp_avg": 22.0,  # Entre 18 et 25
            "consumption": 150.0,  # Inférieur à 2000
        }

        alert_service = AlertService(mock_stats)

        alerts = alert_service.generate_alerts(["salon"])

        assert len(alerts) == 0

    def test_generate_alerts_multiple_locations(self):
        """Test génération d'alertes pour plusieurs locations"""

        mock_stats = Mock(spec=StatsService)

        def side_effect(location):

            if location == "salon":

                return {"temp_avg": 15.0, "consumption": 100.0}

            elif location == "cuisine":

                return {"temp_avg": 28.0, "consumption": 100.0}

            else:

                return {"temp_avg": 22.0, "consumption": 100.0}

        mock_stats.calculate_location_stats.side_effect = side_effect

        alert_service = AlertService(mock_stats)

        alerts = alert_service.generate_alerts(["salon", "cuisine", "chambre"])

        assert len(alerts) >= 2  # Au moins 2 alertes

    def test_generate_alerts_with_none_values(self):
        """Test génération d'alertes avec valeurs None"""

        mock_stats = Mock(spec=StatsService)

        mock_stats.calculate_location_stats.return_value = {"temp_avg": None, "consumption": None}

        alert_service = AlertService(mock_stats)

        alerts = alert_service.generate_alerts(["salon"])

        # Pas d'erreur et pas d'alerte si valeurs None

        assert isinstance(alerts, list)

    def test_alert_structure(self):
        """Test structure des alertes générées"""

        mock_stats = Mock(spec=StatsService)

        mock_stats.calculate_location_stats.return_value = {"temp_avg": 15.0, "consumption": 100.0}

        alert_service = AlertService(mock_stats)

        alerts = alert_service.generate_alerts(["salon"])

        assert len(alerts) > 0

        alert = alerts[0]

        assert "type" in alert

        assert "severity" in alert

        assert "location" in alert

        assert "message" in alert
