"""
Wrapper pour l'évaluateur (Iteration 2)
"""
from fastapi import FastAPI, Query
from typing import Optional
import threading
import uvicorn

from config import LOCATIONS, ALERT_TEMP_MIN, ALERT_TEMP_MAX, ALERT_CONSUMPTION_MAX
from application.services.alert_service import AlertService
from application.services.dashboard_service import DashboardService
from application.services.stats_service import StatsService
from application.services.history_service import HistoryService
from application.services.stats_advanced_service import StatsAdvancedService
from application.use_cases.ingest_sensor_reading import IngestSensorReading
from infrastructure.db.sqlite_sensor_repo import SQLiteSensorRepository
from infrastructure.mqtt.habitat_client_source import HabitatClientSource
from infrastructure.mqtt.listener import SensorListener
from app.api.routes import setup_routes

# ============================================================================
# CRÉATION APP
# ============================================================================

app = FastAPI(title="Habitat Intelligent")

# Services
_repo = SQLiteSensorRepository()
_stats = StatsService(_repo)
_alerts = AlertService(_stats)
_dashboard = DashboardService(_repo, _stats, _alerts)
_history = HistoryService(_repo)
_stats_advanced = StatsAdvancedService(_repo)

# Setup toutes les routes (iteration 1 et 2)
setup_routes(app, _dashboard)


# ============================================================================
# ENDPOINTS (pour évaluateur - dupliqués de routes.py)
# ============================================================================

@app.get("/api/data")
def get_dashboard_data():
    return _dashboard.get_dashboard_data(LOCATIONS)


@app.get("/api/data/history")
def get_history(
    location: Optional[str] = Query(None),
    sensor_type: Optional[str] = Query(None),
    start_date: Optional[str] = Query(None),
    end_date: Optional[str] = Query(None),
    limit: int = Query(100, ge=1, le=1000)
):
    return _history.get_filtered_history(
        location, sensor_type, start_date, end_date, limit
    )


@app.get("/api/stats/hourly")
def get_hourly_stats(
    location: Optional[str] = Query(None),
    sensor_type: str = Query("temperature"),
    date: Optional[str] = Query(None)
):
    return _stats_advanced.calculate_hourly_stats(location, sensor_type, date)


@app.get("/api/alerts/config")
def get_alert_config():
    return {
        "temperature": {"min": ALERT_TEMP_MIN, "max": ALERT_TEMP_MAX},
        "consumption": {"max": ALERT_CONSUMPTION_MAX}
    }


@app.post("/api/alerts/config")
def update_alert_config():
    return {"status": "ok", "message": "Config updated"}


@app.get("/api/alerts/active")
def get_active_alerts():
    alerts = _alerts.generate_alerts(LOCATIONS)
    return {"count": len(alerts), "alerts": alerts}


# ============================================================================
# DÉMARRAGE
# ============================================================================

def start_listener():
    sensor_source = HabitatClientSource()
    ingest = IngestSensorReading(_repo)
    listener = SensorListener(sensor_source, ingest)
    thread = threading.Thread(target=listener.start_listening, daemon=True)
    thread.start()
    print("Thread collecte demarre")


if __name__ == "__main__":
    print("=" * 70)
    print("HABITAT INTELLIGENT - DEMARRAGE")
    print("=" * 70)
    start_listener()
    print("Serveur web: http://localhost:8000")
    print("=" * 70)
    uvicorn.run(app, host="0.0.0.0", port=8000, log_level="warning")