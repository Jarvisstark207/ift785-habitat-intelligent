"""Tests API pour validation des réponses et formats"""
import json
from datetime import datetime

import pytest
from fastapi.testclient import TestClient

from app import app  # IMPORTANT: grâce au pont dans app/__init__.py
from infrastructure.db.sqlite_sensor_repo import SQLiteSensorRepository
from domain.models.sensor_reading import SensorReading


@pytest.fixture
def client():
    """Client de test FastAPI"""
    return TestClient(app)


@pytest.fixture(autouse=True)
def setup_test_data(temp_db, monkeypatch):
    """Configure DB de test avec données"""

    # Rediriger la DB vers la DB temporaire
    monkeypatch.setattr("config.DB_NAME", temp_db)
    monkeypatch.setattr("infrastructure.db.sqlite_connection.DB_NAME", temp_db)

    repo = SQLiteSensorRepository()

    # Insérer données variées
    for i in range(15):
        timestamp = datetime.now().isoformat()

        repo.save(
            SensorReading(
                sensor_id=f"temp_{i}",
                location="salon",
                type="temperature",
                value=20.0 + i * 0.5,
                unit="°C",
                timestamp=timestamp,
            )
        )

        repo.save(
            SensorReading(
                sensor_id=f"power_{i}",
                location="salon",
                type="consommation",
                value=100.0 + i * 10,
                unit="W",
                timestamp=timestamp,
            )
        )

    yield


class TestAPIResponseValidation:
    """Tests pour validation format et contenu des réponses API"""

    def test_dashboard_response_structure(self, client):
        """Test structure complète réponse dashboard"""
        response = client.get("/api/data")

        assert response.status_code == 200
        data = response.json()

        required_keys = ["global", "locations", "alerts", "recent"]
        for key in required_keys:
            assert key in data, f"Clé manquante: {key}"

    def test_dashboard_global_stats_format(self, client):
        """Test format stats globales"""
        response = client.get("/api/data")
        data = response.json()

        global_stats = data["global"]
        assert "total_consumption" in global_stats
        assert "occupied_rooms" in global_stats
        assert "avg_temp" in global_stats

        assert isinstance(global_stats["occupied_rooms"], int)
        if global_stats["total_consumption"] is not None:
            assert isinstance(global_stats["total_consumption"], (int, float))

    def test_dashboard_locations_format(self, client):
        """Test format données par location"""
        response = client.get("/api/data")
        data = response.json()

        locations = data["locations"]
        assert isinstance(locations, dict)

        for location, stats in locations.items():
            assert isinstance(location, str)
            assert isinstance(stats, dict)

    def test_history_response_pagination(self, client):
        """Test pagination réponse historique"""
        response = client.get("/api/data/history?limit=5")

        assert response.status_code == 200
        data = response.json()

        assert "count" in data
        assert "data" in data
        assert len(data["data"]) <= 5

    def test_history_filter_validation(self, client):
        """Test validation des filtres historique"""
        response = client.get("/api/data/history?location=salon&sensor_type=temperature")
        assert response.status_code == 200

        data = response.json()
        assert data["filters"]["location"] == "salon"
        assert data["filters"]["sensor_type"] == "temperature"

    def test_history_date_format_validation(self, client):
        """Test validation format dates"""
        response = client.get("/api/data/history?start_date=2026-01-01T00:00:00")
        assert response.status_code == 200

        data = response.json()
        assert data["filters"]["start_date"] == "2026-01-01T00:00:00"

    def test_hourly_stats_response_format(self, client):
        """Test format réponse stats horaires"""
        today = datetime.now().strftime("%Y-%m-%d")
        response = client.get(f"/api/stats/hourly?date={today}")

        assert response.status_code == 200
        data = response.json()

        assert "date" in data
        assert "hourly_stats" in data
        assert isinstance(data["hourly_stats"], list)

    def test_hourly_stats_entry_format(self, client):
        """Test format entrée stats horaires"""
        today = datetime.now().strftime("%Y-%m-%d")
        response = client.get(f"/api/stats/hourly?date={today}")

        assert response.status_code == 200
        data = response.json()

        if len(data["hourly_stats"]) > 0:
            entry = data["hourly_stats"][0]
            required_fields = ["hour", "avg", "min", "max", "count"]
            for field in required_fields:
                assert field in entry, f"Champ manquant: {field}"

    def test_alert_config_response_format(self, client):
        """Test format configuration alertes"""
        response = client.get("/api/alerts/config")

        assert response.status_code == 200
        data = response.json()

        assert "temperature" in data
        assert "consumption" in data

        assert "min" in data["temperature"]
        assert "max" in data["temperature"]
        assert "max" in data["consumption"]

    def test_alert_config_values_types(self, client):
        """Test types de valeurs config alertes"""
        response = client.get("/api/alerts/config")
        data = response.json()

        assert isinstance(data["temperature"]["min"], (int, float))
        assert isinstance(data["temperature"]["max"], (int, float))
        assert isinstance(data["consumption"]["max"], (int, float))

    def test_active_alerts_response_format(self, client):
        """Test format alertes actives"""
        response = client.get("/api/alerts/active")

        assert response.status_code == 200
        data = response.json()

        assert "count" in data
        assert "alerts" in data
        assert isinstance(data["alerts"], list)
        assert data["count"] == len(data["alerts"])

    def test_active_alerts_entry_format(self, client):
        """Test format entrée alerte active"""
        response = client.get("/api/alerts/active")
        data = response.json()

        if len(data["alerts"]) > 0:
            alert = data["alerts"][0]
            required_fields = ["type", "severity", "location", "message"]
            for field in required_fields:
                assert field in alert, f"Champ manquant dans alerte: {field}"

    def test_response_headers(self, client):
        """Test headers HTTP des réponses"""
        response = client.get("/api/data")

        assert response.status_code == 200
        assert response.headers["content-type"].startswith("application/json")

    def test_limit_parameter_validation(self, client):
        """Test validation paramètre limit"""
        assert client.get("/api/data/history?limit=50").status_code == 200
        assert client.get("/api/data/history?limit=1").status_code == 200
        assert client.get("/api/data/history?limit=1000").status_code == 200

    def test_invalid_limit_parameter(self, client):
        """Test paramètre limit invalide"""
        response = client.get("/api/data/history?limit=2000")
        assert response.status_code in [200, 422]

    def test_json_serialization(self, client):
        """Test sérialisation JSON correcte"""
        response = client.get("/api/data")
        assert response.status_code == 200

        try:
            json.loads(response.text)
        except json.JSONDecodeError:
            pytest.fail("Réponse n'est pas du JSON valide")

    def test_numeric_precision(self, client):
        """Test précision des valeurs numériques"""
        response = client.get("/api/data")
        data = response.json()

        if data["global"]["avg_temp"] is not None:
            temp_str = str(data["global"]["avg_temp"])
            if "." in temp_str:
                decimals = len(temp_str.split(".")[1])
                assert decimals <= 2, "Trop de décimales"

    def test_timestamp_format_in_responses(self, client):
        """Test format timestamps dans réponses"""
        response = client.get("/api/data/history?limit=1")
        assert response.status_code == 200

        data = response.json()
        if len(data["data"]) > 0:
            ts = data["data"][0]["timestamp"]
            try:
                datetime.fromisoformat(ts)
            except ValueError:
                pytest.fail(f"Timestamp invalide: {ts}")
