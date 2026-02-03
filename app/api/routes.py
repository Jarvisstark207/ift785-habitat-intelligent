"""Configuration de toutes les routes FastAPI - Iteration 1 et 2"""
from fastapi import FastAPI, Query
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from starlette.requests import Request
from typing import Optional

from application.services.dashboard_service import DashboardService
from application.services.history_service import HistoryService
from application.services.stats_advanced_service import StatsAdvancedService
from application.services.alert_service import AlertService
from application.services.stats_service import StatsService
from infrastructure.db.sqlite_sensor_repo import SQLiteSensorRepository
from config import LOCATIONS, ALERT_TEMP_MIN, ALERT_TEMP_MAX, ALERT_CONSUMPTION_MAX


def setup_routes(app: FastAPI, dashboard_service: DashboardService) -> None:
    """Configure toutes les routes FastAPI (iteration 1 et 2)"""

    # Fichiers statiques et templates
    app.mount("/static", StaticFiles(directory="static"), name="static")
    templates = Jinja2Templates(directory="templates")

    # Services iteration 2
    _repo = SQLiteSensorRepository()
    _history = HistoryService(_repo)
    _stats_advanced = StatsAdvancedService(_repo)
    _stats = StatsService(_repo)
    _alerts = AlertService(_stats)

    # ========================================================================
    # ITERATION 1 - Dashboard
    # ========================================================================

    @app.get("/api/data")
    def get_dashboard_data():
        """API JSON pour dashboard"""
        return dashboard_service.get_dashboard_data(LOCATIONS)

    @app.get("/", response_class=HTMLResponse)
    def homepage(request: Request):
        """Page HTML dashboard"""
        return templates.TemplateResponse("index.html", {"request": request})

    # ========================================================================
    # ITERATION 2 - Historique et Statistiques
    # ========================================================================

    @app.get("/api/data/history")
    def get_history(
            location: Optional[str] = Query(None, description="Filter by location"),
            sensor_type: Optional[str] = Query(None, description="Filter by sensor type"),
            start_date: Optional[str] = Query(None, description="Start date (ISO)"),
            end_date: Optional[str] = Query(None, description="End date (ISO)"),
            limit: int = Query(100, ge=1, le=1000, description="Max results")
    ):
        """Récupère l'historique filtré"""
        return _history.get_filtered_history(
            location=location,
            sensor_type=sensor_type,
            start_date=start_date,
            end_date=end_date,
            limit=limit
        )

    @app.get("/api/stats/hourly")
    def get_hourly_stats(
            location: Optional[str] = Query(None),
            sensor_type: str = Query("temperature"),
            date: Optional[str] = Query(None, description="Date (YYYY-MM-DD)")
    ):
        """Statistiques horaires"""
        return _stats_advanced.calculate_hourly_stats(
            location=location,
            sensor_type=sensor_type,
            date=date
        )

    # ========================================================================
    # ITERATION 2 - Configuration Alertes
    # ========================================================================

    @app.get("/api/alerts/config")
    def get_alert_config():
        """Configuration alertes"""
        return {
            "temperature": {"min": ALERT_TEMP_MIN, "max": ALERT_TEMP_MAX},
            "consumption": {"max": ALERT_CONSUMPTION_MAX}
        }

    @app.post("/api/alerts/config")
    def update_alert_config():
        """Modifier configuration alertes"""
        return {"status": "ok", "message": "Config updated"}

    @app.get("/api/alerts/active")
    def get_active_alerts():
        """Alertes actives"""
        alerts = _alerts.generate_alerts(LOCATIONS)
        return {"count": len(alerts), "alerts": alerts}