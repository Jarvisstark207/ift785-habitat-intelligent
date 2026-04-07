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

    @app.get("/api/events/history")
    @aspect_log(level="DEBUG")
    def get_event_history():
        """Retourne l'historique des événements du bus (iter 9)"""
        history = EventBus.instance().get_history()
        return {"count": len(history), "events": history}

    @app.get("/api/events/subscribers")
    def get_event_subscribers():
        """Liste les abonnés de chaque événement (iter 9)"""
        return EventBus.instance().all_subscribers()

    @app.post("/api/cache/invalidate")
    def invalidate_cache_endpoint(body: dict = None):
        """Invalide tout ou partie du cache (iter 9)"""
        prefix = (body or {}).get("prefix", "")
        count = invalidate_cache(prefix)
        return {"status": "ok", "invalidated": count}

    @app.get("/api/cache/stats")
    def get_cache_stats():
        """Retourne les statistiques du cache (iter 9)"""
        store = get_cache_store()
        return {"count": len(store), "entries": store}

    # -----------------------------------------------------------------------
    # ITERATION 9 BONUS - Pages UI EventBus live + Cache admin
    # -----------------------------------------------------------------------

    @app.get("/events/live", response_class=HTMLResponse)
    def page_events_live(request: Request):
        """Page UI — flux live des événements publiés sur l'EventBus"""
        return templates.TemplateResponse("events_live.html", {"request": request})

    @app.get("/admin/cache", response_class=HTMLResponse)
    def page_admin_cache(request: Request):
        """Page UI — visualisation du cache, TTL restant et taux de hits"""
        return templates.TemplateResponse("admin_cache.html", {"request": request})

    @app.post("/api/devices/admin/create")
    @log_call
    @require_role("admin")
    @validate_input(DeviceCreateSchema)
    async def admin_create_device(data: DeviceCreateSchema):
        """Crée un device — réservé aux administrateurs (iter 8)"""
        config = data.model_dump()
        device = _device_service.build_device(config)
        return {"status": "ok", "device": device.to_dict()}

    @app.get("/api/devices/admin/list")
    @log_call
    @require_role("admin")
    async def admin_list_devices():
        """Liste tous les devices — réservé aux administrateurs (iter 8)"""
        devices = _device_service.get_all_devices()
        return {
            "count": len(devices),
            "devices": [d.to_dict() for d in devices],
        }

    # -----------------------------------------------------------------------

    @app.get("/api/devices/{device_id}")
    def get_device(device_id: str):
        """Récupère un device"""
        try:
            device = _device_service.get_device(device_id)
            return {"status": "ok", "device": device.to_dict()}
        except ValueError as e:
            return {"status": "error", "message": str(e)}

    @app.get("/api/devices/type/{device_type}")
    def get_devices_by_type(device_type: str):
        """Récupère les devices d'un type"""
        devices = _device_service.get_devices_by_type(device_type)
        return {
            "device_type": device_type,
            "count": len(devices),
            "devices": [device.to_dict() for device in devices],
        }

    @app.get("/api/devices/room/{room_name}")
    def get_devices_by_room(room_name: str):
        """Récupère les devices d'une pièce"""
        devices = _device_service.get_devices_by_room(room_name)
        return {
            "room": room_name,
            "count": len(devices),
            "devices": [device.to_dict() for device in devices],
        }

    @app.get("/api/devices/manufacturer/{manufacturer}")
    def get_devices_by_manufacturer(manufacturer: str):
        """Récupère les devices d'un fabricant"""
        devices = _device_service.get_devices_by_manufacturer(manufacturer)
        return {
            "manufacturer": manufacturer,
            "count": len(devices),
            "devices": [device.to_dict() for device in devices],
        }

    @app.delete("/api/devices/{device_id}")
    def delete_device(device_id: str):
        """Supprime un device"""
        if _device_service.delete_device(device_id):
            return {"status": "ok", "message": f"Device {device_id} deleted"}
        else:
            return {"status": "error", "message": f"Device {device_id} not found"}

    @app.put("/api/devices/{device_id}")
    def update_device(device_id: str, config: dict):
        """Met à jour un device"""
        try:
            device = _device_service.get_device(device_id)
            # Mettre à jour les propriétés
            if "name" in config:
                device.name = config["name"]
            if "brightness" in config and hasattr(device, "brightness"):
                device.brightness = config["brightness"]
            if "color" in config and hasattr(device, "color"):
                device.color = config["color"]
            if "temperature" in config and hasattr(device, "temperature"):
                device.temperature = config["temperature"]
            if "target_temperature" in config and hasattr(device, "target_temperature"):
                device.target_temperature = config["target_temperature"]
            if "mode" in config and hasattr(device, "mode"):
                device.mode = config["mode"]
            if "ppm" in config and hasattr(device, "ppm"):
                device.ppm = config["ppm"]
            if "alarm_threshold" in config and hasattr(device, "alarm_threshold"):
                device.alarm_threshold = config["alarm_threshold"]
            if "motion_detected" in config and hasattr(device, "motion_detected"):
                device.motion_detected = config["motion_detected"]
            if "sensitivity" in config and hasattr(device, "sensitivity"):
                device.sensitivity = config["sensitivity"]
            return {"status": "ok", "device": device.to_dict()}
        except ValueError as e:
            return {"status": "error", "message": str(e)}

    @app.get("/api/devices/paginated/list")
    def list_devices_paginated(
        skip: int = Query(0, ge=0, description="Nombre de devices à ignorer"),
        limit: int = Query(10, ge=1, le=100, description="Nombre max de devices"),
    ):
        """Liste les devices avec pagination"""
        all_devices = _device_service.get_all_devices()
        total = len(all_devices)
        devices = all_devices[skip:skip + limit]
        return {
            "total": total,
            "skip": skip,
            "limit": limit,
            "count": len(devices),
            "devices": [device.to_dict() for device in devices],
        }

    @app.get("/api/devices/search/advanced")
    def search_devices(
        device_type: Optional[str] = Query(None, description="Filtrer par type"),
        room_name: Optional[str] = Query(None, description="Filtrer par pièce"),
        manufacturer: Optional[str] = Query(None, description="Filtrer par fabricant"),
        skip: int = Query(0, ge=0, description="Nombre de devices à ignorer"),
        limit: int = Query(10, ge=1, le=100, description="Nombre max de devices"),
    ):
        """Recherche avancée de devices avec filtres multiples"""
        all_devices = _device_service.get_all_devices()

        # Appliquer les filtres
        if device_type:
            all_devices = [d for d in all_devices if d.device_type == device_type]
        if room_name:
            all_devices = [d for d in all_devices if d.room_name == room_name]
        if manufacturer:
            all_devices = [
                d for d in all_devices if d.manufacturer.lower() == manufacturer.lower()
            ]

        total = len(all_devices)
        devices = all_devices[skip:skip + limit]

        return {
            "total": total,
            "skip": skip,
            "limit": limit,
            "count": len(devices),
            "filters": {
                "device_type": device_type,
                "room_name": room_name,
                "manufacturer": manufacturer,
            },
            "devices": [device.to_dict() for device in devices],
        }

    @app.get("/api/devices/stats/summary")
    def get_devices_stats():
        """Obtient un résumé des statistiques des devices"""
        all_devices = _device_service.get_all_devices()

        # Compter par type
        types_count = {}
        for device in all_devices:
            types_count[device.device_type] = types_count.get(device.device_type, 0) + 1

        # Compter par pièce
        rooms_count = {}
        for device in all_devices:
            rooms_count[device.room_name] = rooms_count.get(device.room_name, 0) + 1

        # Compter par fabricant
        manufacturers_count = {}
        for device in all_devices:
            manufacturers_count[device.manufacturer] = (
                manufacturers_count.get(device.manufacturer, 0) + 1
            )

        return {
            "total_devices": len(all_devices),
            "by_type": types_count,
            "by_room": rooms_count,
            "by_manufacturer": manufacturers_count,
        }

    @app.get("/api/devices/stats/types")
    def get_devices_stats_by_type():
        """Obtient les statistiques détaillées par type"""
        devices_by_type = {}
        for device in _device_service.get_all_devices():
            if device.device_type not in devices_by_type:
                devices_by_type[device.device_type] = {
                    "count": 0,
                    "devices": [],
                }
            devices_by_type[device.device_type]["count"] += 1
            devices_by_type[device.device_type]["devices"].append(device.to_dict())

        return {"by_type": devices_by_type}

    @app.get("/api/devices/stats/rooms")
    def get_devices_stats_by_room():
        """Obtient les statistiques détaillées par pièce"""
        devices_by_room = {}
        for device in _device_service.get_all_devices():
            if device.room_name not in devices_by_room:
                devices_by_room[device.room_name] = {
                    "count": 0,
                    "devices": [],
                }
            devices_by_room[device.room_name]["count"] += 1
            devices_by_room[device.room_name]["devices"].append(device.to_dict())

        return {"by_room": devices_by_room}

    @app.get("/api/devices/stats/manufacturers")
    def get_devices_stats_by_manufacturer():
        """Obtient les statistiques détaillées par fabricant"""
        devices_by_manufacturer = {}
        for device in _device_service.get_all_devices():
            manufacturer = device.manufacturer
            if manufacturer not in devices_by_manufacturer:
                devices_by_manufacturer[manufacturer] = {
                    "count": 0,
                    "devices": [],
                }
            devices_by_manufacturer[manufacturer]["count"] += 1
            devices_by_manufacturer[manufacturer]["devices"].append(
                device.to_dict()
            )

        return {"by_manufacturer": devices_by_manufacturer}
