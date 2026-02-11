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
from domain.models.alert_config import AlertConfigUpdate
from infrastructure.db.sqlite_sensor_repo import SQLiteSensorRepository
from config import LOCATIONS


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
