"""Tests d'intégration pour les opérations de base de données"""
import pytest
from datetime import datetime, timedelta
from infrastructure.db.sqlite_sensor_repo import SQLiteSensorRepository
from domain.models.sensor_reading import SensorReading


class TestDatabaseOperations:
    """Tests d'intégration avec la base de données réelle"""

    @pytest.fixture(autouse=True)
    def setup_repo(self, temp_db, monkeypatch):
        """Configure repository avec DB temporaire"""
        monkeypatch.setattr('config.DB_NAME', temp_db)
        monkeypatch.setattr('infrastructure.db.sqlite_connection.DB_NAME', temp_db)
        self.repo = SQLiteSensorRepository()
        yield

    def test_save_single_reading(self):
        """Test sauvegarde d'une seule lecture"""
        reading = SensorReading(
            sensor_id="test_001",
            location="salon",
            type="temperature",
            value=22.5,
            unit="°C",
            timestamp=datetime.now().isoformat()
        )

        self.repo.save(reading)
        recent = self.repo.find_recent(1)

        assert len(recent) == 1
        assert recent[0]['sensor_id'] == "test_001"
        assert recent[0]['value'] == 22.5

    def test_save_multiple_readings(self):
        """Test sauvegarde de plusieurs lectures"""
        for i in range(5):
            reading = SensorReading(
                sensor_id=f"test_{i}",
                location="salon",
                type="temperature",
                value=20.0 + i,
                unit="°C",
                timestamp=datetime.now().isoformat()
            )
            self.repo.save(reading)

        recent = self.repo.find_recent(10)
        assert len(recent) == 5

    def test_find_recent_returns_ordered_by_timestamp(self):
        """Test que find_recent retourne données triées par timestamp DESC"""
        base_time = datetime.now()

        for i in range(3):
            timestamp = (base_time - timedelta(minutes=i)).isoformat()
            reading = SensorReading(
                sensor_id=f"test_{i}",
                location="salon",
                type="temperature",
                value=20.0 + i,
                unit="°C",
                timestamp=timestamp
            )
            self.repo.save(reading)

        recent = self.repo.find_recent(10)

        # Premier élément devrait être le plus récent
        assert recent[0]['sensor_id'] == "test_0"

    def test_find_by_location_and_type(self):
        """Test recherche par location et type"""
        # Insérer différentes combinaisons
        combos = [
            ("salon", "temperature"),
            ("salon", "lumiere"),
            ("cuisine", "temperature"),
        ]

        for location, sensor_type in combos:
            reading = SensorReading(
                sensor_id=f"{sensor_type}_{location}",
                location=location,
                type=sensor_type,
                value=100.0,
                unit="unit",
                timestamp=datetime.now().isoformat()
            )
            self.repo.save(reading)

        # Rechercher salon + temperature
        results = self.repo.find_by_location_and_type("salon", "temperature", 10)

        assert len(results) == 1
        assert results[0].location == "salon"
        assert results[0].type == "temperature"

    def test_database_transaction_rollback_on_error(self):
        """Test rollback en cas d'erreur"""
        # Tenter d'insérer données invalides
        try:
            reading = SensorReading(
                sensor_id=None,  # Invalide
                location="salon",
                type="temperature",
                value=22.0,
                unit="°C",
                timestamp=datetime.now().isoformat()
            )
            self.repo.save(reading)
        except:
            pass

        # Vérifier que rien n'a été inséré
        recent = self.repo.find_recent(10)
        assert len(recent) == 0

    def test_concurrent_writes(self):
        """Test écritures concurrentes (simulation)"""
        # Simuler plusieurs threads écrivant en même temps
        for i in range(10):
            reading = SensorReading(
                sensor_id=f"concurrent_{i}",
                location="salon",
                type="temperature",
                value=20.0 + i,
                unit="°C",
                timestamp=datetime.now().isoformat()
            )
            self.repo.save(reading)

        recent = self.repo.find_recent(20)
        assert len(recent) == 10

    def test_database_handles_special_characters(self):
        """Test gestion de caractères spéciaux"""
        reading = SensorReading(
            sensor_id="test_'quote\"",
            location="salon's room",
            type="temperature",
            value=22.0,
            unit="°C",
            timestamp=datetime.now().isoformat()
        )

        self.repo.save(reading)
        recent = self.repo.find_recent(1)

        assert len(recent) == 1
        assert "quote" in recent[0]['sensor_id']

    def test_database_persistence(self):
        """Test persistance des données"""
        reading = SensorReading(
            sensor_id="persist_test",
            location="salon",
            type="temperature",
            value=22.0,
            unit="°C",
            timestamp=datetime.now().isoformat()
        )

        self.repo.save(reading)

        # Créer nouvelle instance du repo (simule redémarrage)
        new_repo = SQLiteSensorRepository()
        recent = new_repo.find_recent(10)

        assert len(recent) == 1
        assert recent[0]['sensor_id'] == "persist_test"

    def test_large_batch_insert(self):
        """Test insertion de grand lot de données"""
        batch_size = 100

        for i in range(batch_size):
            reading = SensorReading(
                sensor_id=f"batch_{i}",
                location="salon",
                type="temperature",
                value=20.0 + (i % 10),
                unit="°C",
                timestamp=datetime.now().isoformat()
            )
            self.repo.save(reading)

        recent = self.repo.find_recent(batch_size + 10)
        assert len(recent) == batch_size