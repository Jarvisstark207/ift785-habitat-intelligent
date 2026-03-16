"""Tests pour la couche infrastructure"""
import sqlite3
import os
import pytest
from unittest.mock import MagicMock, patch
from domain.models.sensor_reading import SensorReading
from infrastructure.db.sqlite_connection import SQLiteConnection
from infrastructure.db.sqlite_sensor_repo import SQLiteSensorRepository
from infrastructure.mqtt.listener import SensorListener
from infrastructure.mqtt.habitat_client_source import HabitatClientSource


# ─── Helpers ──────────────────────────────────────────────────────────────────

SCHEMA_SQL = """
    CREATE TABLE sensor_readings (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        sensor_id TEXT NOT NULL,
        location TEXT NOT NULL,
        type TEXT NOT NULL,
        value REAL,
        unit TEXT,
        timestamp TEXT NOT NULL,
        received_at DATETIME DEFAULT CURRENT_TIMESTAMP
    )
"""


def create_test_db(path):
    """Crée un fichier SQLite avec le schéma requis"""
    conn = sqlite3.connect(path)
    conn.execute(SCHEMA_SQL)
    conn.commit()
    conn.close()


def make_reading(
    sensor_id="s1",
    location="salon",
    type_="temperature",
    value=22.5,
    unit="C",
    timestamp="2024-01-01T10:00:00"
):
    return SensorReading(sensor_id, location, type_, value, unit, timestamp)


@pytest.fixture
def db_path(tmp_path):
    """Fournit un chemin vers une DB de test temporaire"""
    path = str(tmp_path / "test.db")
    create_test_db(path)
    return path


@pytest.fixture
def repo(db_path):
    """Repository configuré sur la DB de test"""
    with patch("infrastructure.db.sqlite_connection.DB_NAME", db_path):
        yield SQLiteSensorRepository()


# ─── Tests SQLiteConnection ────────────────────────────────────────────────────

class TestSQLiteConnection:

    def test_get_connection_retourne_connexion(self, db_path):
        with patch("infrastructure.db.sqlite_connection.DB_NAME", db_path):
            conn = SQLiteConnection.get_connection()
            assert conn is not None
            conn.close()

    def test_get_connection_row_factory(self, db_path):
        with patch("infrastructure.db.sqlite_connection.DB_NAME", db_path):
            conn = SQLiteConnection.get_connection()
            assert conn.row_factory == sqlite3.Row
            conn.close()


# ─── Tests SQLiteSensorRepository – save / find ───────────────────────────────

class TestSQLiteSensorRepositorySave:

    def test_save_insere_lecture(self, db_path):
        repo = SQLiteSensorRepository()
        reading = make_reading()

        with patch("infrastructure.db.sqlite_connection.DB_NAME", db_path):
            repo.save(reading)

        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM sensor_readings")
        rows = cursor.fetchall()
        conn.close()

        assert len(rows) == 1
        assert rows[0][1] == "s1"      # sensor_id
        assert rows[0][2] == "salon"   # location
        assert rows[0][3] == "temperature"
        assert rows[0][4] == 22.5

    def test_save_plusieurs_lectures(self, db_path):
        repo = SQLiteSensorRepository()

        with patch("infrastructure.db.sqlite_connection.DB_NAME", db_path):
            repo.save(make_reading(sensor_id="s1", location="salon"))
            repo.save(make_reading(sensor_id="s2", location="cuisine"))

        conn = sqlite3.connect(db_path)
        count = conn.execute(
            "SELECT COUNT(*) FROM sensor_readings"
        ).fetchone()[0]
        conn.close()
        assert count == 2


class TestSQLiteSensorRepositoryFind:

    def test_find_recent_retourne_liste(self, db_path):
        repo = SQLiteSensorRepository()
        with patch("infrastructure.db.sqlite_connection.DB_NAME", db_path):
            repo.save(make_reading())
            result = repo.find_recent(10)

        assert isinstance(result, list)
        assert len(result) == 1
        assert result[0]["sensor_id"] == "s1"

    def test_find_recent_vide(self, db_path):
        repo = SQLiteSensorRepository()
        with patch("infrastructure.db.sqlite_connection.DB_NAME", db_path):
            result = repo.find_recent(10)
        assert result == []

    def test_find_recent_respecte_limite(self, db_path):
        repo = SQLiteSensorRepository()
        with patch("infrastructure.db.sqlite_connection.DB_NAME", db_path):
            for i in range(5):
                ts = f"2024-01-01T10:0{i}:00"
                repo.save(make_reading(sensor_id=f"s{i}", timestamp=ts))
            result = repo.find_recent(3)
        assert len(result) == 3

    def test_find_by_location_and_type(self, db_path):
        repo = SQLiteSensorRepository()
        with patch("infrastructure.db.sqlite_connection.DB_NAME", db_path):
            repo.save(make_reading(location="salon", type_="temperature"))
            repo.save(make_reading(
                location="cuisine", type_="temperature", sensor_id="s2"
            ))
            result = repo.find_by_location_and_type("salon", "temperature")

        assert len(result) == 1
        assert isinstance(result[0], SensorReading)
        assert result[0].location == "salon"

    def test_find_by_location_and_type_vide(self, db_path):
        repo = SQLiteSensorRepository()
        with patch("infrastructure.db.sqlite_connection.DB_NAME", db_path):
            result = repo.find_by_location_and_type("salon", "temperature")
        assert result == []

    def test_find_temperature_history(self, db_path):
        repo = SQLiteSensorRepository()
        with patch("infrastructure.db.sqlite_connection.DB_NAME", db_path):
            repo.save(make_reading(
                location="salon", type_="temperature", value=21.0
            ))
            history = repo.find_temperature_history(["salon"])

        assert "salon" in history
        assert len(history["salon"]) == 1
        assert history["salon"][0]["value"] == 21.0

    def test_find_consumption_current_avec_donnees(self, db_path):
        repo = SQLiteSensorRepository()
        with patch("infrastructure.db.sqlite_connection.DB_NAME", db_path):
            repo.save(make_reading(
                type_="consommation", value=150.0, unit="W"
            ))
            result = repo.find_consumption_current(["salon"])
        assert result["salon"] == 150.0

    def test_find_consumption_current_sans_donnees(self, db_path):
        repo = SQLiteSensorRepository()
        with patch("infrastructure.db.sqlite_connection.DB_NAME", db_path):
            result = repo.find_consumption_current(["salon"])
        assert result["salon"] == 0


# ─── Tests SQLiteSensorRepository – stats ─────────────────────────────────────

class TestSQLiteSensorRepositoryStats:

    def test_get_stats_sans_donnees(self, db_path):
        repo = SQLiteSensorRepository()
        with patch("infrastructure.db.sqlite_connection.DB_NAME", db_path):
            stats = repo.get_stats_for_location("salon")

        assert stats["temp_avg"] is None
        assert stats["luminosity"] is None
        assert stats["movement"] is False
        assert stats["consumption"] is None

    def test_get_stats_avec_temperature(self, db_path):
        repo = SQLiteSensorRepository()
        with patch("infrastructure.db.sqlite_connection.DB_NAME", db_path):
            repo.save(make_reading(type_="temperature", value=22.0))
            repo.save(make_reading(
                sensor_id="s2", type_="temperature", value=24.0,
                timestamp="2024-01-01T10:01:00"
            ))
            stats = repo.get_stats_for_location("salon")

        assert stats["temp_avg"] is not None
        assert stats["temp_min"] == 22.0
        assert stats["temp_max"] == 24.0

    def test_get_stats_avec_lumiere(self, db_path):
        repo = SQLiteSensorRepository()
        with patch("infrastructure.db.sqlite_connection.DB_NAME", db_path):
            repo.save(make_reading(type_="lumiere", value=300.0, unit="lux"))
            stats = repo.get_stats_for_location("salon")
        assert stats["luminosity"] == 300

    def test_get_stats_avec_consommation(self, db_path):
        repo = SQLiteSensorRepository()
        with patch("infrastructure.db.sqlite_connection.DB_NAME", db_path):
            repo.save(make_reading(type_="consommation", value=100.0, unit="W"))
            stats = repo.get_stats_for_location("salon")
        assert stats["consumption"] == 100.0

    def test_get_total_consumption(self, db_path):
        repo = SQLiteSensorRepository()
        with patch("infrastructure.db.sqlite_connection.DB_NAME", db_path):
            repo.save(make_reading(
                location="salon", type_="consommation", value=100.0, unit="W"
            ))
            repo.save(make_reading(
                sensor_id="s2", location="cuisine",
                type_="consommation", value=200.0, unit="W"
            ))
            total = repo.get_total_consumption(["salon", "cuisine"])
        assert total == 300.0

    def test_get_total_consumption_vide(self, db_path):
        repo = SQLiteSensorRepository()
        with patch("infrastructure.db.sqlite_connection.DB_NAME", db_path):
            total = repo.get_total_consumption(["salon"])
        assert total == 0.0

    def test_get_occupied_rooms_count(self, db_path):
        repo = SQLiteSensorRepository()
        with patch("infrastructure.db.sqlite_connection.DB_NAME", db_path):
            count = repo.get_occupied_rooms_count()
        assert count == 0

    def test_get_average_temperature_une_location(self, db_path):
        repo = SQLiteSensorRepository()
        with patch("infrastructure.db.sqlite_connection.DB_NAME", db_path):
            repo.save(make_reading(type_="temperature", value=22.0))
            avg = repo.get_average_temperature(["salon"])
        assert avg == 22.0

    def test_get_average_temperature_plusieurs_locations(self, db_path):
        repo = SQLiteSensorRepository()
        with patch("infrastructure.db.sqlite_connection.DB_NAME", db_path):
            repo.save(make_reading(
                location="salon", type_="temperature", value=20.0
            ))
            repo.save(make_reading(
                sensor_id="s2", location="cuisine",
                type_="temperature", value=24.0
            ))
            avg = repo.get_average_temperature(["salon", "cuisine"])
        assert avg == 22.0

    def test_get_average_temperature_vide(self, db_path):
        repo = SQLiteSensorRepository()
        with patch("infrastructure.db.sqlite_connection.DB_NAME", db_path):
            avg = repo.get_average_temperature(["salon"])
        assert avg is None


# ─── Tests SensorListener ─────────────────────────────────────────────────────

class TestSensorListener:

    def test_creation(self):
        source = MagicMock()
        ingest = MagicMock()
        listener = SensorListener(source, ingest)
        assert listener._source is source
        assert listener._ingest is ingest

    def test_start_listening_mode_simulation(self):
        source = MagicMock()
        source.is_simulation_mode.return_value = True
        reading = make_reading()
        source.get_next_reading.side_effect = [reading, SystemExit]

        ingest = MagicMock()
        listener = SensorListener(source, ingest)

        with pytest.raises(SystemExit):
            listener.start_listening()

        ingest.execute.assert_called_once_with(reading)

    def test_start_listening_mode_reel(self):
        source = MagicMock()
        source.is_simulation_mode.return_value = False
        source.get_next_reading.side_effect = SystemExit

        ingest = MagicMock()
        listener = SensorListener(source, ingest)

        with pytest.raises(SystemExit):
            listener.start_listening()

    def test_start_listening_gere_exception(self):
        source = MagicMock()
        source.is_simulation_mode.return_value = True
        source.get_next_reading.side_effect = [
            ValueError("erreur lecture"),
            SystemExit
        ]

        ingest = MagicMock()
        listener = SensorListener(source, ingest)

        with patch("time.sleep"), pytest.raises(SystemExit):
            listener.start_listening()

        ingest.execute.assert_not_called()


# ─── Tests HabitatClientSource ────────────────────────────────────────────────

class TestHabitatClientSource:

    def test_get_next_reading(self):
        sensor_data = MagicMock()
        sensor_data.sensor_id = "s1"
        sensor_data.location = "salon"
        sensor_data.type = "temperature"
        sensor_data.value = 22.5
        sensor_data.unit = "C"
        sensor_data.timestamp = "2024-01-01T10:00:00"

        mock_client = MagicMock()
        mock_client.get_next_sensor_data.return_value = sensor_data

        with patch(
            "infrastructure.mqtt.habitat_client_source.HabitatClient",
            return_value=mock_client
        ):
            source = HabitatClientSource()
            reading = source.get_next_reading()

        assert isinstance(reading, SensorReading)
        assert reading.sensor_id == "s1"
        assert reading.location == "salon"

    def test_is_simulation_mode_vrai(self):
        mock_client = MagicMock()
        mock_client.is_simulation_mode.return_value = True

        with patch(
            "infrastructure.mqtt.habitat_client_source.HabitatClient",
            return_value=mock_client
        ):
            source = HabitatClientSource()
            assert source.is_simulation_mode() is True

    def test_is_simulation_mode_faux(self):
        mock_client = MagicMock()
        mock_client.is_simulation_mode.return_value = False

        with patch(
            "infrastructure.mqtt.habitat_client_source.HabitatClient",
            return_value=mock_client
        ):
            source = HabitatClientSource()
            assert source.is_simulation_mode() is False