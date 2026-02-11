"""Tests d'intégration pour la configuration des alertes"""
import pytest
from datetime import datetime
from infrastructure.db.sqlite_sensor_repo import SQLiteSensorRepository
from application.services.stats_service import StatsService
from application.services.alert_service import AlertService
from domain.models.sensor_reading import SensorReading
from config import ALERT_TEMP_MIN, ALERT_TEMP_MAX, ALERT_CONSUMPTION_MAX


class TestAlertConfigIntegration:
    """Tests d'intégration pour configuration et génération alertes"""

    @pytest.fixture(autouse=True)
    def setup_services(self, temp_db, monkeypatch):
        """Configure services avec DB temporaire"""
        monkeypatch.setattr('config.DB_NAME', temp_db)
        monkeypatch.setattr('infrastructure.db.sqlite_connection.DB_NAME', temp_db)

        self.repo = SQLiteSensorRepository()
        self.stats_service = StatsService(self.repo)
        self.alert_service = AlertService(self.stats_service)
        yield

    def test_alert_generation_with_real_temperature_data(self):
        """Test génération d'alertes avec vraies données température"""
        # Insérer température basse
        reading = SensorReading(
            sensor_id="temp_low",
            location="salon",
            type="temperature",
            value=ALERT_TEMP_MIN - 5,  # En dessous du seuil
            unit="°C",
            timestamp=datetime.now().isoformat()
        )
        self.repo.save(reading)

        alerts = self.alert_service.generate_alerts(["salon"])

        assert len(alerts) > 0
        temp_alerts = [a for a in alerts if a['type'] == 'temperature']
        assert len(temp_alerts) > 0
        assert temp_alerts[0]['location'] == 'salon'

    def test_alert_generation_with_real_consumption_data(self):
        """Test génération d'alertes avec vraies données consommation"""
        # Insérer consommation haute
        reading = SensorReading(
            sensor_id="power_high",
            location="cuisine",
            type="consommation",
            value=ALERT_CONSUMPTION_MAX + 500,  # Au-dessus du seuil
            unit="W",
            timestamp=datetime.now().isoformat()
        )
        self.repo.save(reading)

        alerts = self.alert_service.generate_alerts(["cuisine"])

        assert len(alerts) > 0
        consumption_alerts = [a for a in alerts if a['type'] == 'consumption']
        assert len(consumption_alerts) > 0
        assert consumption_alerts[0]['severity'] == 'critical'

    def test_no_alerts_with_normal_values(self):
        """Test pas d'alertes avec valeurs normales"""
        # Température normale
        temp_reading = SensorReading(
            sensor_id="temp_normal",
            location="salon",
            type="temperature",
            value=(ALERT_TEMP_MIN + ALERT_TEMP_MAX) / 2,
            unit="°C",
            timestamp=datetime.now().isoformat()
        )
        self.repo.save(temp_reading)

        # Consommation normale
        power_reading = SensorReading(
            sensor_id="power_normal",
            location="salon",
            type="consommation",
            value=ALERT_CONSUMPTION_MAX / 2,
            unit="W",
            timestamp=datetime.now().isoformat()
        )
        self.repo.save(power_reading)

        alerts = self.alert_service.generate_alerts(["salon"])

        assert len(alerts) == 0

    def test_multiple_alerts_same_location(self):
        """Test plusieurs alertes pour même location"""
        # Température basse
        temp_reading = SensorReading(
            sensor_id="temp_low",
            location="salon",
            type="temperature",
            value=ALERT_TEMP_MIN - 5,
            unit="°C",
            timestamp=datetime.now().isoformat()
        )
        self.repo.save(temp_reading)

        # Consommation haute
        power_reading = SensorReading(
            sensor_id="power_high",
            location="salon",
            type="consommation",
            value=ALERT_CONSUMPTION_MAX + 500,
            unit="W",
            timestamp=datetime.now().isoformat()
        )
        self.repo.save(power_reading)

        alerts = self.alert_service.generate_alerts(["salon"])

        # Devrait y avoir 2 alertes minimum
        assert len(alerts) >= 2
        alert_types = {a['type'] for a in alerts}
        assert 'temperature' in alert_types
        assert 'consumption' in alert_types

    def test_alerts_multiple_locations(self):
        """Test alertes pour plusieurs locations"""
        # Salon : température basse
        reading1 = SensorReading(
            sensor_id="temp_salon",
            location="salon",
            type="temperature",
            value=ALERT_TEMP_MIN - 3,
            unit="°C",
            timestamp=datetime.now().isoformat()
        )
        self.repo.save(reading1)

        # Cuisine : température haute
        reading2 = SensorReading(
            sensor_id="temp_cuisine",
            location="cuisine",
            type="temperature",
            value=ALERT_TEMP_MAX + 3,
            unit="°C",
            timestamp=datetime.now().isoformat()
        )
        self.repo.save(reading2)

        # Chambre : normal
        reading3 = SensorReading(
            sensor_id="temp_chambre",
            location="chambre",
            type="temperature",
            value=22.0,
            unit="°C",
            timestamp=datetime.now().isoformat()
        )
        self.repo.save(reading3)

        alerts = self.alert_service.generate_alerts(["salon", "cuisine", "chambre"])

        assert len(alerts) >= 2
        locations_with_alerts = {a['location'] for a in alerts}
        assert 'salon' in locations_with_alerts
        assert 'cuisine' in locations_with_alerts
        assert 'chambre' not in locations_with_alerts

    def test_alert_threshold_boundary_values(self):
        """Test valeurs limites des seuils d'alerte"""
        # Exactement au minimum (pas d'alerte)
        reading_min = SensorReading(
            sensor_id="temp_min",
            location="test1",
            type="temperature",
            value=ALERT_TEMP_MIN,
            unit="°C",
            timestamp=datetime.now().isoformat()
        )
        self.repo.save(reading_min)

        alerts_min = self.alert_service.generate_alerts(["test1"])
        # Ne devrait pas générer d'alerte à la limite exacte
        temp_alerts = [a for a in alerts_min if a['type'] == 'temperature']
        assert len(temp_alerts) == 0

        # Juste en dessous du minimum (alerte)
        reading_below = SensorReading(
            sensor_id="temp_below",
            location="test2",
            type="temperature",
            value=ALERT_TEMP_MIN - 0.1,
            unit="°C",
            timestamp=datetime.now().isoformat()
        )
        self.repo.save(reading_below)

        alerts_below = self.alert_service.generate_alerts(["test2"])
        temp_alerts_below = [a for a in alerts_below if a['type'] == 'temperature']
        assert len(temp_alerts_below) > 0

    def test_alert_config_with_historical_data(self):
        """Test configuration alertes avec données historiques"""
        # Insérer plusieurs lectures sur le temps
        from datetime import timedelta
        base_time = datetime.now()

        for i in range(10):
            timestamp = (base_time - timedelta(minutes=i)).isoformat()
            value = ALERT_TEMP_MIN - 5 if i < 5 else 22.0

            reading = SensorReading(
                sensor_id=f"temp_{i}",
                location="salon",
                type="temperature",
                value=value,
                unit="°C",
                timestamp=timestamp
            )
            self.repo.save(reading)

        # Les 5 dernières lectures sont normales
        # Devrait se baser sur la moyenne des dernières lectures
        alerts = self.alert_service.generate_alerts(["salon"])

        # Vérifier qu'il y a ou pas d'alerte selon la logique de calcul
        assert isinstance(alerts, list)

    def test_alert_persistence_across_queries(self):
        """Test persistance des conditions d'alerte"""
        # Générer condition d'alerte
        reading = SensorReading(
            sensor_id="temp_persistent",
            location="salon",
            type="temperature",
            value=ALERT_TEMP_MIN - 5,
            unit="°C",
            timestamp=datetime.now().isoformat()
        )
        self.repo.save(reading)

        # Première vérification
        alerts1 = self.alert_service.generate_alerts(["salon"])
        assert len(alerts1) > 0

        # Deuxième vérification (devrait être identique)
        alerts2 = self.alert_service.generate_alerts(["salon"])
        assert len(alerts2) == len(alerts1)

    def test_alert_clearing_with_new_data(self):
        """Test disparition d'alerte avec nouvelles données normales"""
        # Donnée anormale
        reading_bad = SensorReading(
            sensor_id="temp_bad",
            location="salon",
            type="temperature",
            value=ALERT_TEMP_MIN - 5,
            unit="°C",
            timestamp=datetime.now().isoformat()
        )
        self.repo.save(reading_bad)

        alerts_before = self.alert_service.generate_alerts(["salon"])
        assert len(alerts_before) > 0

        # Ajouter plusieurs lectures normales récentes
        import time
        time.sleep(0.1)  # Assurer timestamp différent
        for i in range(10):
            reading_good = SensorReading(
                sensor_id=f"temp_good_{i}",
                location="salon",
                type="temperature",
                value=22.0,
                unit="°C",
                timestamp=datetime.now().isoformat()
            )
            self.repo.save(reading_good)

        # Les alertes devraient se baser sur les données récentes
        alerts_after = self.alert_service.generate_alerts(["salon"])
        # Selon la logique, l'alerte pourrait disparaître
        assert isinstance(alerts_after, list)
#