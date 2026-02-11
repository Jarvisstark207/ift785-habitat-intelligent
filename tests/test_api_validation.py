"""Tests de validation des APIs FastAPI"""

import sys
import importlib.util
from pathlib import Path
from datetime import datetime, timedelta
from starlette.testclient import TestClient

import pytest

from domain.models.alert_config import (
    AlertConfigUpdate,
    TemperatureConfig,
    ConsumptionConfig,
)

# Load app.py from root directory
app_path = Path(__file__).parent.parent / "app.py"
spec = importlib.util.spec_from_file_location("app_module", app_path)
app_module = importlib.util.module_from_spec(spec)
sys.modules["app_module"] = app_module
spec.loader.exec_module(app_module)

# Load app and models
app = app_module.app


@pytest.fixture
def client():
    """Client de test FastAPI"""
    return TestClient(app)


# ========================================================================
# TESTS ITERATION 1 - DASHBOARD DATA
# ========================================================================


class TestDashboardAPI:
    """Tests pour l'endpoint /api/data"""

    def test_get_dashboard_data_success(self, client):
        """Vérifie que /api/data retourne des données valides"""
        response = client.get("/api/data")

        assert response.status_code == 200
        data = response.json()

        # Vérifier structure de base
        assert isinstance(data, dict)
        assert "locations" in data
        # locations peut être dict ou list
        assert isinstance(data["locations"], (dict, list))

    def test_get_dashboard_data_no_params(self, client):
        """Vérifie que /api/data fonctionne sans paramètres"""
        response = client.get("/api/data")
        assert response.status_code == 200

    def test_get_dashboard_data_response_format(self, client):
        """Vérifie le format de réponse JSON"""
        response = client.get("/api/data")
        assert response.headers["content-type"] == "application/json"


class TestHomepage:
    """Tests pour la page d'accueil"""

    def test_homepage_returns_html(self, client):
        """Vérifie que / retourne du HTML"""
        response = client.get("/")

        assert response.status_code == 200
        assert "text/html" in response.headers["content-type"]

    def test_homepage_contains_content(self, client):
        """Vérifie que la page HTML contient du contenu"""
        response = client.get("/")

        content = response.text
        assert len(content) > 0
        assert isinstance(content, str)


# ========================================================================
# TESTS ITERATION 2 - HISTORIQUE
# ========================================================================


class TestHistoryAPI:
    """Tests pour l'endpoint /api/data/history"""

    def test_get_history_no_filters(self, client):
        """Récupère l'historique sans filtres"""
        response = client.get("/api/data/history")

        assert response.status_code == 200
        data = response.json()

        # Doit être une liste ou dict valide
        assert data is not None

    def test_get_history_with_location_filter(self, client):
        """Filtre par location"""
        response = client.get("/api/data/history?location=salon")

        assert response.status_code == 200
        data = response.json()
        assert data is not None

    def test_get_history_with_sensor_type_filter(self, client):
        """Filtre par type de capteur"""
        response = client.get("/api/data/history?sensor_type=temperature")

        assert response.status_code == 200
        data = response.json()
        assert data is not None

    def test_get_history_with_date_range(self, client):
        """Filtre par plage de dates"""
        today = datetime.now().date()
        start_date = str(today - timedelta(days=7))
        end_date = str(today)

        response = client.get(
            f"/api/data/history?start_date={start_date}&end_date={end_date}"
        )

        assert response.status_code == 200

    def test_get_history_with_limit(self, client):
        """Teste le paramètre limit"""
        response = client.get("/api/data/history?limit=50")

        assert response.status_code == 200

    def test_get_history_limit_min_validation(self, client):
        """Vérifie que limit >= 1 est validé"""
        response = client.get("/api/data/history?limit=0")

        # Doit être rejeté (validation Pydantic)
        assert response.status_code == 422

    def test_get_history_limit_max_validation(self, client):
        """Vérifie que limit <= 1000 est validé"""
        response = client.get("/api/data/history?limit=2000")

        # Doit être rejeté (validation Pydantic)
        assert response.status_code == 422

    def test_get_history_all_filters_combined(self, client):
        """Combine tous les filtres"""
        today = datetime.now().date()
        start_date = str(today - timedelta(days=1))
        end_date = str(today)

        response = client.get(
            f"/api/data/history?"
            f"location=salon&"
            f"sensor_type=temperature&"
            f"start_date={start_date}&"
            f"end_date={end_date}&"
            f"limit=100"
        )

        assert response.status_code == 200
        data = response.json()
        assert data is not None


# ========================================================================
# TESTS ITERATION 2 - STATISTIQUES HORAIRES
# ========================================================================


class TestHourlyStatsAPI:
    """Tests pour l'endpoint /api/stats/hourly"""

    def test_get_hourly_stats_default(self, client):
        """Récupère les stats horaires avec paramètres par défaut"""
        response = client.get("/api/stats/hourly")

        assert response.status_code == 200
        data = response.json()
        assert data is not None

    def test_get_hourly_stats_with_location(self, client):
        """Récupère les stats pour une location spécifique"""
        response = client.get("/api/stats/hourly?location=salon")

        assert response.status_code == 200
        data = response.json()
        assert data is not None

    def test_get_hourly_stats_with_sensor_type(self, client):
        """Change le type de capteur"""
        response = client.get("/api/stats/hourly?sensor_type=lumiere")

        assert response.status_code == 200
        data = response.json()
        assert data is not None

    def test_get_hourly_stats_with_date(self, client):
        """Spécifie une date"""
        today = datetime.now().date()
        response = client.get(f"/api/stats/hourly?date={today}")

        assert response.status_code == 200
        data = response.json()
        assert data is not None

    def test_get_hourly_stats_all_params(self, client):
        """Combine tous les paramètres"""
        today = datetime.now().date()
        response = client.get(
            f"/api/stats/hourly?"
            f"location=cuisine&"
            f"sensor_type=consommation&"
            f"date={today}"
        )

        assert response.status_code == 200
        data = response.json()
        assert data is not None

    def test_get_hourly_stats_sensor_types(self, client):
        """Teste différents types de capteurs"""
        sensor_types = ["temperature", "lumiere", "consommation", "mouvement"]

        for sensor_type in sensor_types:
            response = client.get(f"/api/stats/hourly?sensor_type={sensor_type}")
            assert response.status_code == 200


# ========================================================================
# TESTS ITERATION 2 - ALERTES CONFIG
# ========================================================================


class TestAlertConfigAPI:
    """Tests pour les endpoints de configuration d'alertes"""

    def test_get_alert_config(self, client):
        """Récupère la configuration des alertes"""
        response = client.get("/api/alerts/config")

        assert response.status_code == 200
        data = response.json()

        # Doit retourner une configuration valide
        assert isinstance(data, dict)

    def test_get_alert_config_contains_temperature(self, client):
        """Vérifie que la config contient les seuils de température"""
        response = client.get("/api/alerts/config")
        data = response.json()

        # Doit avoir des infos de température
        assert "temperature" in data or "temp_min" in data or "temp_max" in data

    def test_get_alert_config_contains_consumption(self, client):
        """Vérifie que la config contient les seuils de consommation"""
        response = client.get("/api/alerts/config")
        data = response.json()

        # Doit avoir des infos de consommation
        assert "consumption" in data or "consumption_max" in data

    def test_update_alert_config_temperature_min(self, client):
        """Met à jour le seuil min de température"""
        config = AlertConfigUpdate(temperature=TemperatureConfig(min=15.0))

        response = client.post("/api/alerts/config", json=config.model_dump())

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "ok"
        assert "new_config" in data

    def test_update_alert_config_temperature_max(self, client):
        """Met à jour le seuil max de température"""
        config = AlertConfigUpdate(temperature=TemperatureConfig(max=30.0))

        response = client.post("/api/alerts/config", json=config.model_dump())

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "ok"

    def test_update_alert_config_both_temperature(self, client):
        """Met à jour les deux seuils de température"""
        config = AlertConfigUpdate(temperature=TemperatureConfig(min=15.0, max=30.0))

        response = client.post("/api/alerts/config", json=config.model_dump())

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "ok"

    def test_update_alert_config_consumption_max(self, client):
        """Met à jour le seuil max de consommation"""
        config = AlertConfigUpdate(consumption=ConsumptionConfig(max=500.0))

        response = client.post("/api/alerts/config", json=config.model_dump())

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "ok"

    def test_update_alert_config_all_parameters(self, client):
        """Met à jour tous les paramètres"""
        config = AlertConfigUpdate(
            temperature=TemperatureConfig(min=15.0, max=30.0),
            consumption=ConsumptionConfig(max=500.0),
        )

        response = client.post("/api/alerts/config", json=config.model_dump())

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "ok"
        assert data["message"] == "Config updated"

    def test_update_alert_config_temperature_validation_min(self, client):
        """Vérifie la validation - temp min >= 0"""
        # La validation Pydantic se fait avant l'envoi HTTP
        # On teste qu'une valeur invalide lève une ValidationError
        from pydantic_core import ValidationError
        with pytest.raises(ValidationError):
            _ = AlertConfigUpdate(
                temperature=TemperatureConfig(min=-5.0)
            )

    def test_update_alert_config_temperature_validation_max(self, client):
        """Vérifie la validation - temp max <= 50"""
        # La validation Pydantic se fait avant l'envoi HTTP
        # On teste qu'une valeur invalide lève une ValidationError
        from pydantic_core import ValidationError
        with pytest.raises(ValidationError):
            _ = AlertConfigUpdate(
                temperature=TemperatureConfig(max=55.0)
            )

    def test_update_alert_config_consumption_validation(self, client):
        """Vérifie la validation - consumption >= 0"""
        # La validation Pydantic se fait avant l'envoi HTTP
        # On teste qu'une valeur invalide lève une ValidationError
        from pydantic_core import ValidationError
        with pytest.raises(ValidationError):
            _ = AlertConfigUpdate(
                consumption=ConsumptionConfig(max=-100.0)
            )


# ========================================================================
# TESTS ITERATION 2 - ALERTES ACTIVES
# ========================================================================


class TestActiveAlertsAPI:
    """Tests pour l'endpoint /api/alerts/active"""

    def test_get_active_alerts(self, client):
        """Récupère les alertes actives"""
        response = client.get("/api/alerts/active")

        assert response.status_code == 200
        data = response.json()

        # Doit contenir count et alerts
        assert "count" in data
        assert "alerts" in data

    def test_get_active_alerts_count_is_integer(self, client):
        """Vérifie que count est un entier"""
        response = client.get("/api/alerts/active")
        data = response.json()

        assert isinstance(data["count"], int)
        assert data["count"] >= 0

    def test_get_active_alerts_alerts_is_list(self, client):
        """Vérifie que alerts est une liste"""
        response = client.get("/api/alerts/active")
        data = response.json()

        assert isinstance(data["alerts"], list)

    def test_get_active_alerts_count_matches_list_length(self, client):
        """Vérifie que count correspond à la longueur de la liste"""
        response = client.get("/api/alerts/active")
        data = response.json()

        assert data["count"] == len(data["alerts"])


# ========================================================================
# TESTS GÉNÉRAUX
# ========================================================================


class TestAPIValidation:
    """Tests de validation générale des APIs"""

    def test_invalid_endpoint_returns_404(self, client):
        """Vérifie qu'un endpoint invalide retourne 404"""
        response = client.get("/api/invalid/endpoint")

        assert response.status_code == 404

    def test_api_response_content_type(self, client):
        """Vérifie que les APIs retournent du JSON"""
        endpoints = [
            "/api/data",
            "/api/data/history",
            "/api/stats/hourly",
            "/api/alerts/config",
            "/api/alerts/active",
        ]

        for endpoint in endpoints:
            response = client.get(endpoint)
            assert response.status_code == 200
            assert "application/json" in response.headers["content-type"]

    def test_post_methods_accept_json(self, client):
        """Vérifie que les méthodes POST acceptent du JSON"""
        config = AlertConfigUpdate(temperature=TemperatureConfig(min=10.0))

        response = client.post(
            "/api/alerts/config",
            json=config.model_dump(),
            headers={"Content-Type": "application/json"},
        )

        assert response.status_code == 200

    def test_api_methods_only_get_allowed_on_history(self, client):
        """Vérifie que /api/data/history n'accepte que GET"""
        response = client.post("/api/data/history")

        # POST n'est pas autorisé
        assert response.status_code == 405

    def test_api_methods_only_post_allowed_on_alert_config_update(self, client):
        """Vérifie que POST est accepté pour les alertes"""
        config = AlertConfigUpdate()
        response = client.post("/api/alerts/config", json=config.model_dump())

        # POST doit être autorisé
        assert response.status_code in [200, 422]  # 200 ou validation error

    def test_empty_config_update_is_valid(self, client):
        """Vérifie qu'une config vide est valide"""
        config = AlertConfigUpdate()

        response = client.post("/api/alerts/config", json=config.model_dump())

        # Doit être acceptée
        assert response.status_code == 200

    def test_null_values_in_config(self, client):
        """Vérifie que None/null est accepté"""
        config_data = {"temperature": None, "consumption": None}

        response = client.post("/api/alerts/config", json=config_data)

        assert response.status_code == 200


# ========================================================================
# TESTS D'INTÉGRATION
# ========================================================================


class TestAPIIntegration:
    """Tests d'intégration entre APIs"""

    def test_get_config_then_update(self, client):
        """Récupère la config actuelle puis la met à jour"""
        # Récupérer config
        response_get = client.get("/api/alerts/config")
        assert response_get.status_code == 200

        # Mettre à jour
        config = AlertConfigUpdate(temperature=TemperatureConfig(min=12.0, max=28.0))
        response_post = client.post("/api/alerts/config", json=config.model_dump())
        assert response_post.status_code == 200

    def test_get_stats_then_check_alerts(self, client):
        """Récupère les stats puis les alertes"""
        # Récupérer stats
        response_stats = client.get("/api/stats/hourly")
        assert response_stats.status_code == 200

        # Vérifier alertes
        response_alerts = client.get("/api/alerts/active")
        assert response_alerts.status_code == 200

    def test_history_then_stats(self, client):
        """Récupère l'historique puis les stats"""
        # Historique
        response_history = client.get("/api/data/history?limit=50")
        assert response_history.status_code == 200

        # Stats
        response_stats = client.get("/api/stats/hourly")
        assert response_stats.status_code == 200

    def test_dashboard_then_all_endpoints(self, client):
        """Teste le dashboard puis tous les endpoints"""
        # Dashboard
        response_dashboard = client.get("/api/data")
        assert response_dashboard.status_code == 200

        # Historique
        response_history = client.get("/api/data/history")
        assert response_history.status_code == 200

        # Stats
        response_stats = client.get("/api/stats/hourly")
        assert response_stats.status_code == 200

        # Alertes
        response_alerts = client.get("/api/alerts/active")
        assert response_alerts.status_code == 200

        # Config
        response_config = client.get("/api/alerts/config")
        assert response_config.status_code == 200
