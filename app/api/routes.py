"""Configuration de toutes les routes FastAPI - Iteration 1 et 2"""

from fastapi import FastAPI, Query
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel
from starlette.requests import Request
from typing import Optional

from application.services.dashboard_service import DashboardService
from application.services.history_service import HistoryService
from application.services.stats_advanced_service import StatsAdvancedService
from application.services.alert_service import AlertService
from application.services.stats_service import StatsService
from domain.models.alert_config import AlertConfigUpdate
from infrastructure.db.sqlite_sensor_repo import SQLiteSensorRepository
from config import LOCATIONS

# Iter 8 - Méta-programmation
from app.core.decorators import log_call, validate_input, require_role
from app.core import log_store
from domain.models.device_meta import DeviceMeta

# Iter 9 - AOP
from app.core.aspects import aspect_log, aspect_cache, aspect_retry, aspect_audit
from app.core.aspects import get_cache_store, invalidate_cache
from app.core.event_bus import EventBus, on_event


class DeviceCreateSchema(BaseModel):
    """Schéma Pydantic pour la création d'un device (iter 8)."""
    device_id: str
    name: str
    room_name: str
    device_type: str
    manufacturer: str = "Generic"


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
        limit: int = Query(100, ge=1, le=1000, description="Max results"),
    ):
        """Récupère l'historique filtré"""
        return _history.get_filtered_history(
            location=location,
            sensor_type=sensor_type,
            start_date=start_date,
            end_date=end_date,
            limit=limit,
        )

    @app.get("/api/stats/hourly")
    def get_hourly_stats(
        location: Optional[str] = Query(None),
        sensor_type: str = Query("temperature"),
        date: Optional[str] = Query(None, description="Date (YYYY-MM-DD)"),
    ):
        """Statistiques horaires"""
        return _stats_advanced.calculate_hourly_stats(
            location=location, sensor_type=sensor_type, date=date
        )

    # ========================================================================
    # ITERATION 2 - Configuration Alertes
    # ========================================================================

    @app.get("/api/alerts/config")
    def get_alert_config():
        """Configuration alertes"""
        return _alerts.get_config()

    @app.post("/api/alerts/config")
    def update_alert_config(config: AlertConfigUpdate):
        """Modifier configuration alertes"""
        updated_config = {}

        if config.temperature:
            if config.temperature.min is not None:
                updated_config["temp_min"] = config.temperature.min
            if config.temperature.max is not None:
                updated_config["temp_max"] = config.temperature.max

        if config.consumption and config.consumption.max is not None:
            updated_config["consumption_max"] = config.consumption.max

        result = _alerts.update_config(**updated_config)

        return {"status": "ok", "message": "Config updated", "new_config": result}

    @app.get("/api/alerts/active")
    def get_active_alerts():
        """Alertes actives"""
        alerts = _alerts.generate_alerts(LOCATIONS)
        return {"count": len(alerts), "alerts": alerts}

    # ========================================================================
    # ITERATION 3 - Device Management (Factory, Abstract Factory, Builder, Singleton)
    # ========================================================================

    from application.services.device_service import DeviceService

    _device_service = DeviceService()

    @app.post("/api/devices/build")
    def build_device(config: dict):
        """Construit un device avec le builder pattern"""
        try:
            device = _device_service.build_device(config)
            return {"status": "ok", "device": device.to_dict()}
        except ValueError as e:
            return {"status": "error", "message": str(e)}

    @app.get("/api/devices")
    def list_devices():
        """Liste tous les devices"""
        devices = _device_service.get_all_devices()
        return {
            "count": len(devices),
            "devices": [device.to_dict() for device in devices],
        }

    # ========================================================================
    # ITERATION 8 - Méta-programmation (décorateurs + métaclasse)
    # ========================================================================

    @app.get("/api/devices/types")
    @log_call
    def list_device_types():
        """Liste tous les types de devices enregistrés par métaclasse"""
        registry = DeviceMeta.device_registry
        return {
            "count": len(registry),
            "types": list(registry.keys()),
        }

    @app.get("/api/devices/types/{type_name}/info")
    @log_call
    def get_device_type_info(type_name: str):
        """Introspection d'un type de device enregistré (champs, validations)"""
        from app.core.descriptors import TypedField, RangedField
        cls = DeviceMeta.registry.get(type_name)
        if cls is None:
            from fastapi import HTTPException
            raise HTTPException(status_code=404, detail=f"Type '{type_name}' inconnu")
        fields = []
        validations = []
        for name, val in vars(cls).items():
            if name.startswith("_"):
                continue
            if isinstance(val, TypedField):
                fields.append(name)
                info = f"{name}: TypedField({val.expected_type.__name__}"
                if val.max_length:
                    info += f", max={val.max_length}"
                if val.allowed:
                    info += f", allowed={val.allowed}"
                info += ")"
                validations.append(info)
            elif isinstance(val, RangedField):
                fields.append(name)
                validations.append(
                    f"{name}: RangedField([{val.min_val}, {val.max_val}])"
                )
        return {
            "name": type_name,
            "module": cls.__module__,
            "fields": fields,
            "validations": validations,
            "has_to_dict": hasattr(cls, "to_dict"),
        }

    # -----------------------------------------------------------------------
    # ITERATION 8 BONUS - Pages UI (DeviceRegistry + Logs transversaux)
    # -----------------------------------------------------------------------

    @app.get("/devices/registry", response_class=HTMLResponse)
    def page_device_registry(request: Request):
        """Page UI — visualisation des types enregistrés par DeviceMeta"""
        return templates.TemplateResponse(
            "device_registry.html", {"request": request}
        )

    @app.get("/admin/logs", response_class=HTMLResponse)
    def page_admin_logs(request: Request):
        """Page UI — journal des appels décorés @log_call"""
        return templates.TemplateResponse(
            "admin_logs.html", {"request": request}
        )

    @app.get("/api/admin/logs")
    @log_call
    def api_get_logs():
        """API JSON — retourne les entrées du journal @log_call"""
        entries = log_store.get_entries()
        return {"count": len(entries), "entries": entries}

    @app.delete("/api/admin/logs")
    def api_clear_logs():
        """Vide le journal des logs (utile pour les tests / reset UI)"""
        log_store.clear()
        return {"status": "ok", "message": "Journal vidé"}

    # ========================================================================
    # ITERATION 9 - AOP (Aspects transversaux + EventBus)
    # ========================================================================

    @app.get("/api/sensors/latest")
    @aspect_log(level="INFO")
    @aspect_cache(ttl=30.0, key_fn=lambda: "sensors:latest")
    def get_sensors_latest():
        """Dernières lectures capteurs — résultat mis en cache 30s (@aspect_cache)"""
        readings = _repo.find_recent(limit=20)
        return {"count": len(readings), "readings": readings}

    @app.get("/api/devices/summary")
    @aspect_log(level="INFO")
    @aspect_cache(ttl=60.0, key_fn=lambda: "devices:summary")
    def get_devices_summary():
        """Résumé des devices — résultat mis en cache 60s (@aspect_cache)"""
        all_devices = _device_service.get_all_devices()
        by_type: dict = {}
        by_room: dict = {}
        for d in all_devices:
            by_type[d.device_type] = by_type.get(d.device_type, 0) + 1
            by_room[d.room_name] = by_room.get(d.room_name, 0) + 1
        return {
            "total": len(all_devices),
            "by_type": by_type,
            "by_room": by_room,
        }

    @app.post("/api/events/publish")
    @aspect_log(level="INFO")
    @aspect_audit(level="INFO", action="event.published")
    def publish_event(body: dict):
        """Publie un événement sur le bus déclaratif (iter 9)"""
        event_name = body.get("event", "")
        payload = body.get("payload", {})
        if not event_name:
            from fastapi import HTTPException
            raise HTTPException(status_code=422, detail="event name required")
        EventBus.instance().publish(event_name, payload)
        return {"status": "ok", "event": event_name}
