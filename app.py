#!/usr/bin/env python3
"""
Application Habitat Intelligent - Simple et Procedurale pour la premiere itération IFT785
Utilise ift785_client.py pour recevoir donnees MQTT
"""

import sqlite3
import threading
import time
from datetime import datetime, timedelta
from fastapi import FastAPI
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from starlette.requests import Request
import uvicorn
from ift785_client import HabitatClient
from domain.models.sensor_reading import SensorReading


# ============================================================================
# CONFIGURATION
# ============================================================================
from config import (
    DB_NAME,
    LOCATIONS,
    ALERT_TEMP_MIN,
    ALERT_TEMP_MAX,
    ALERT_CONSUMPTION_MAX,

)


"""
DB_NAME = "habitat_ift785.db"
LOCATIONS = ["salon", "cuisine", "chambre"]
ALERT_TEMP_MIN = 18.0
ALERT_TEMP_MAX = 25.0
ALERT_CONSUMPTION_MAX = 2000.0
MOVEMENT_TIMEOUT_SEC = 300
"""
# ============================================================================
# CONNEXION BASE DE DONNEES
# ============================================================================


def get_db_connection():
    """Retourne une connexion SQLite"""
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    return conn


# ============================================================================
# FONCTION INSERTION
# ============================================================================

def insert_sensor_data(reading: SensorReading):
    """Insert sensor reading dans la BD"""
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("""
        INSERT INTO sensor_readings
        (sensor_id, location, type, value, unit, timestamp)
        VALUES (?, ?, ?, ?, ?, ?)
    """, reading.to_db_tuple())

    conn.commit()
    conn.close()

    print(f"Insere: {reading.location}/{reading.type} = {reading.value}")


# ============================================================================
# THREAD MQTT
# ============================================================================

def mqtt_listener_thread():
    """Thread qui ecoute MQTT et insere dans BD"""
    print("Demarrage thread collecte donnees...")

    client = HabitatClient()

    if client.is_simulation_mode():
        print("Mode SIMULATION active")
    else:
        print("Mode MQTT REEL actif")

    while True:
        try:
            sensor_data = client.get_next_sensor_data()
            reading = SensorReading.from_sensor_data(sensor_data)
            insert_sensor_data(reading)
        except Exception as e:
            print(f"Erreur collecte: {e}")
            time.sleep(1)


# ============================================================================
# CALCULS
# ============================================================================

def calculate_location_stats(location):
    """Calcule stats pour une piece (dernieres 10 lectures)"""
    conn = get_db_connection()
    cursor = conn.cursor()

    stats = {}

    # Temperature (moyenne, min, max sur 10 dernieres)
    cursor.execute("""
        SELECT AVG(value), MIN(value), MAX(value)
        FROM (
            SELECT value FROM sensor_readings
            WHERE location = ? AND type = 'temperature'
            ORDER BY timestamp DESC LIMIT 10
        )
    """, (location,))
    row = cursor.fetchone()
    stats['temp_avg'] = round(row[0], 1) if row[0] else None
    stats['temp_min'] = round(row[1], 1) if row[1] else None
    stats['temp_max'] = round(row[2], 1) if row[2] else None

    # Luminosite actuelle
    cursor.execute("""
        SELECT value FROM sensor_readings
        WHERE location = ? AND type = 'lumiere'
        ORDER BY timestamp DESC LIMIT 1
    """, (location,))
    row = cursor.fetchone()
    stats['luminosity'] = int(row[0]) if row else None

    # Mouvement (dernier < 5 min)
    five_min_ago = (datetime.now() - timedelta(minutes=5)).isoformat()
    cursor.execute("""
        SELECT value FROM sensor_readings
        WHERE location = ? AND type = 'mouvement'
        AND timestamp > ?
        ORDER BY timestamp DESC LIMIT 1
    """, (location, five_min_ago))
    row = cursor.fetchone()
    stats['movement'] = bool(row[0]) if row else False

    # Consommation actuelle
    cursor.execute("""
        SELECT value FROM sensor_readings
        WHERE location = ? AND type = 'consommation'
        ORDER BY timestamp DESC LIMIT 1
    """, (location,))
    row = cursor.fetchone()
    stats['consumption'] = round(row[0], 1) if row else None

    conn.close()
    return stats


def calculate_global_stats():
    """Stats globales maison"""
    conn = get_db_connection()
    cursor = conn.cursor()

    # Consommation totale
    total_consumption = 0
    for location in LOCATIONS:
        cursor.execute("""
            SELECT value FROM sensor_readings
            WHERE location = ? AND type = 'consommation'
            ORDER BY timestamp DESC LIMIT 1
        """, (location,))
        row = cursor.fetchone()
        if row and row[0]:
            total_consumption += row[0]

    # Pieces occupees
    five_min_ago = (datetime.now() - timedelta(minutes=5)).isoformat()
    cursor.execute("""
        SELECT COUNT(DISTINCT location) FROM sensor_readings
        WHERE type = 'mouvement' AND value = 1
        AND timestamp > ?
    """, (five_min_ago,))
    occupied_rooms = cursor.fetchone()[0]

    # Temperature moyenne maison
    temps = []
    for location in LOCATIONS:
        cursor.execute("""
            SELECT value FROM sensor_readings
            WHERE location = ? AND type = 'temperature'
            ORDER BY timestamp DESC LIMIT 1
        """, (location,))
        row = cursor.fetchone()
        if row and row[0]:
            temps.append(row[0])

    avg_temp = round(sum(temps) / len(temps), 1) if temps else None

    conn.close()

    return {
        'total_consumption': round(total_consumption, 1),
        'occupied_rooms': occupied_rooms,
        'avg_temp': avg_temp
    }


def get_alerts():
    """Genere alertes simples"""
    alerts = []

    for location in LOCATIONS:
        stats = calculate_location_stats(location)

        if stats['temp_avg']:
            if stats['temp_avg'] < ALERT_TEMP_MIN:
                alerts.append(f"{location}: Temperature basse ({stats['temp_avg']}C)")
            elif stats['temp_avg'] > ALERT_TEMP_MAX:
                alerts.append(f"{location}: Temperature elevee ({stats['temp_avg']}C)")

    global_stats = calculate_global_stats()
    if global_stats['total_consumption'] > ALERT_CONSUMPTION_MAX:
        alerts.append(f"Consommation elevee: {global_stats['total_consumption']}W")

    return alerts


def get_recent_readings(limit=20):
    """Dernieres N lectures"""
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT * FROM sensor_readings
        ORDER BY timestamp DESC LIMIT ?
    """, (limit,))

    rows = cursor.fetchall()
    conn.close()

    return [dict(row) for row in rows]


def get_temperature_history():
    """10 dernieres temperatures par piece pour graphique"""
    conn = get_db_connection()
    cursor = conn.cursor()

    history = {}

    for location in LOCATIONS:
        cursor.execute("""
            SELECT value, timestamp FROM sensor_readings
            WHERE location = ? AND type = 'temperature'
            ORDER BY timestamp DESC LIMIT 10
        """, (location,))

        rows = cursor.fetchall()
        history[location] = [
            {'value': row[0], 'timestamp': row[1]}
            for row in reversed(rows)
        ]

    conn.close()
    return history


def get_consumption_current():
    """Consommation actuelle par piece pour graphique"""
    conn = get_db_connection()
    cursor = conn.cursor()

    consumption = {}

    for location in LOCATIONS:
        cursor.execute("""
            SELECT value FROM sensor_readings
            WHERE location = ? AND type = 'consommation'
            ORDER BY timestamp DESC LIMIT 1
        """, (location,))

        row = cursor.fetchone()
        consumption[location] = round(row[0], 1) if row else 0

    conn.close()
    return consumption


# ============================================================================
# FASTAPI
# ============================================================================

app = FastAPI(title="Habitat Intelligent")
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")


@app.get("/api/data")
def get_dashboard_data():
    """API JSON pour dashboard"""

    locations_data = {}
    for location in LOCATIONS:
        locations_data[location] = calculate_location_stats(location)

    return {
        "global": calculate_global_stats(),
        "locations": locations_data,
        "alerts": get_alerts(),
        "recent": get_recent_readings(20),
        "temperature_history": get_temperature_history(),
        "consumption_current": get_consumption_current()
    }


@app.get("/", response_class=HTMLResponse)
def homepage(request: Request):
    """Page HTML dashboard"""
    return templates.TemplateResponse("index.html", {"request": request})


# ============================================================================
# DEMARRAGE
# ============================================================================

if __name__ == "__main__":
    print("=" * 70)
    print("HABITAT INTELLIGENT - DEMARRAGE")
    print("=" * 70)

    # Demarrer thread MQTT
    mqtt_thread = threading.Thread(target=mqtt_listener_thread, daemon=True)
    mqtt_thread.start()

    print("Thread collecte demarre")
    print("Serveur web: http://localhost:8000")
    print("=" * 70)

    # Demarrer FastAPI
    uvicorn.run(app, host="0.0.0.0", port=8000, log_level="warning")
