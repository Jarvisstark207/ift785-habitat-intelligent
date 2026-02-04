"""Tests unitaires pour le modèle SensorReading"""

from domain.models.sensor_reading import SensorReading


class TestSensorReading:
    """Tests pour le modèle SensorReading"""

    def test_create_sensor_reading_success(self):
        """Test création d'une lecture valide"""

        reading = SensorReading(
            sensor_id="temp_001",
            location="salon",
            type="temperature",
            value=22.5,
            unit="°C",
            timestamp="2026-02-03T10:00:00",
        )

        assert reading.sensor_id == "temp_001"

        assert reading.location == "salon"

        assert reading.type == "temperature"

        assert reading.value == 22.5

        assert reading.unit == "°C"

        assert reading.timestamp == "2026-02-03T10:00:00"

    def test_to_db_tuple(self, sample_reading):
        """Test conversion en tuple pour DB"""

        db_tuple = sample_reading.to_db_tuple()

        assert len(db_tuple) == 6

        assert db_tuple[0] == "temp_001"

        assert db_tuple[1] == "salon"

        assert db_tuple[2] == "temperature"

        assert db_tuple[3] == 22.5

        assert db_tuple[4] == "°C"

        assert db_tuple[5] == "2026-02-03T10:00:00"

    def test_to_dict(self, sample_reading):
        """Test conversion en dictionnaire"""

        result = sample_reading.to_dict()

        assert isinstance(result, dict)

        assert result["sensor_id"] == "temp_001"

        assert result["location"] == "salon"

        assert result["type"] == "temperature"

        assert result["value"] == 22.5

        assert result["unit"] == "°C"

        assert result["timestamp"] == "2026-02-03T10:00:00"

    def test_from_sensor_data(self):
        """Test création depuis objet sensor_data"""

        class MockSensorData:

            sensor_id = "temp_001"

            location = "salon"

            type = "temperature"

            value = 22.5

            unit = "°C"

            timestamp = "2026-02-03T10:00:00"

        mock_data = MockSensorData()

        reading = SensorReading.from_sensor_data(mock_data)

        assert reading.sensor_id == "temp_001"

        assert reading.location == "salon"

        assert reading.type == "temperature"

    def test_sensor_reading_with_different_types(self):
        """Test avec différents types de capteurs"""

        # Température

        temp = SensorReading("t1", "salon", "temperature", 22.5, "°C", "2026-01-01T10:00:00")

        assert temp.type == "temperature"

        # Lumière

        light = SensorReading("l1", "cuisine", "lumiere", 500, "lux", "2026-01-01T10:00:00")

        assert light.type == "lumiere"

        # Consommation

        power = SensorReading("p1", "chambre", "consommation", 150.0, "W", "2026-01-01T10:00:00")

        assert power.type == "consommation"

        # Mouvement

        motion = SensorReading("m1", "salon", "mouvement", 1, "bool", "2026-01-01T10:00:00")

        assert motion.type == "mouvement"
