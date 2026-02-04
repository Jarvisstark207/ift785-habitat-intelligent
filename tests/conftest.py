"""Fixtures pytest partagées pour tous les tests"""

import pytest

import sqlite3

import tempfile

import os

from datetime import datetime, timedelta

from unittest.mock import Mock
 
from domain.models.sensor_reading import SensorReading

from infrastructure.db.sqlite_sensor_repo import SQLiteSensorRepository

from application.services.stats_service import StatsService

from application.services.alert_service import AlertService

from application.services.history_service import HistoryService

from application.services.stats_advanced_service import StatsAdvancedService
 
 
@pytest.fixture

def temp_db():

    """Crée une base de données temporaire pour les tests"""

    fd, path = tempfile.mkstemp(suffix='.db')

    os.close(fd)

    # Créer la table

    conn = sqlite3.connect(path)

    cursor = conn.cursor()

    cursor.execute("""

        CREATE TABLE sensor_readings (

            id INTEGER PRIMARY KEY AUTOINCREMENT,

            sensor_id TEXT NOT NULL,

            location TEXT NOT NULL,

            type TEXT NOT NULL,

            value REAL NOT NULL,

            unit TEXT NOT NULL,

            timestamp TEXT NOT NULL

        )

    """)

    conn.commit()

    conn.close()

    yield path

    # Cleanup

    if os.path.exists(path):

        os.unlink(path)
 
 
@pytest.fixture

def mock_repo():

    """Repository mocké pour tests unitaires"""

    repo = Mock(spec=SQLiteSensorRepository)

    return repo
 
 
@pytest.fixture

def sample_reading():

    """Lecture de capteur exemple"""

    return SensorReading(

        sensor_id="temp_001",

        location="salon",

        type="temperature",

        value=22.5,

        unit="°C",

        timestamp="2026-02-03T10:00:00"

    )
 
 
@pytest.fixture

def sample_readings():

    """Plusieurs lectures pour tests"""

    base_time = datetime.now()

    readings = []

    for i in range(10):

        timestamp = (base_time - timedelta(minutes=i)).isoformat()

        readings.append(SensorReading(

            sensor_id=f"temp_{i:03d}",

            location="salon",

            type="temperature",

            value=20.0 + i * 0.5,

            unit="°C",

            timestamp=timestamp

        ))

    return readings
 
 
@pytest.fixture

def populated_db(temp_db):

    """Base de données avec données de test"""

    conn = sqlite3.connect(temp_db)

    cursor = conn.cursor()

    # Données variées

    base_time = datetime.now()

    locations = ["salon", "cuisine", "chambre"]

    sensor_types = ["temperature", "lumiere", "consommation", "mouvement"]

    for location in locations:

        for i in range(20):

            timestamp = (base_time - timedelta(minutes=i)).isoformat()

            # Température

            cursor.execute("""

                INSERT INTO sensor_readings 

                (sensor_id, location, type, value, unit, timestamp)

                VALUES (?, ?, ?, ?, ?, ?)

            """, (f"temp_{location}_{i}", location, "temperature", 

                  20.0 + i * 0.2, "°C", timestamp))

            # Lumière

            cursor.execute("""

                INSERT INTO sensor_readings 

                (sensor_id, location, type, value, unit, timestamp)

                VALUES (?, ?, ?, ?, ?, ?)

            """, (f"light_{location}_{i}", location, "lumiere", 

                  500 + i * 10, "lux", timestamp))

            # Consommation

            cursor.execute("""

                INSERT INTO sensor_readings 

                (sensor_id, location, type, value, unit, timestamp)

                VALUES (?, ?, ?, ?, ?, ?)

            """, (f"power_{location}_{i}", location, "consommation", 

                  100 + i * 5, "W", timestamp))

            # Mouvement

            cursor.execute("""

                INSERT INTO sensor_readings 

                (sensor_id, location, type, value, unit, timestamp)

                VALUES (?, ?, ?, ?, ?, ?)

            """, (f"motion_{location}_{i}", location, "mouvement", 

                  1 if i < 5 else 0, "bool", timestamp))

    conn.commit()

    conn.close()

    return temp_db
 
 
@pytest.fixture

def stats_service(mock_repo):

    """Service de stats mocké"""

    return StatsService(mock_repo)
 
 
@pytest.fixture

def alert_service(stats_service):

    """Service d'alertes avec stats mocké"""

    return AlertService(stats_service)
 
 
@pytest.fixture

def history_service(mock_repo):

    """Service d'historique mocké"""

    return HistoryService(mock_repo)
 
 
@pytest.fixture

def stats_advanced_service(mock_repo):

    """Service de stats avancées mocké"""

    return StatsAdvancedService(mock_repo)
 
 
@pytest.fixture

def mock_stats_data():

    """Données de stats mockées"""

    return {

        'temp_avg': 22.0,

        'temp_min': 20.0,

        'temp_max': 24.0,

        'luminosity': 500,

        'movement': True,

        'consumption': 150.0

    }
 