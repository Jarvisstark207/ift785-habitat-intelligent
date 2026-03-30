"""
Wrapper pour l'évaluateur (Iteration 2)
"""

from fastapi import FastAPI, Query, Depends
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from starlette.requests import Request
from typing import Optional, List
import threading
import uvicorn

from config import LOCATIONS
from application.services.alert_service import AlertService
from application.services.dashboard_service import DashboardService
from application.services.stats_service import StatsService
from application.services.history_service import HistoryService
from application.services.stats_advanced_service import StatsAdvancedService
from application.use_cases.ingest_sensor_reading import IngestSensorReading
from domain.models.alert_config import AlertConfigUpdate
from infrastructure.db.sqlite_sensor_repo import SQLiteSensorRepository
from infrastructure.mqtt.habitat_client_source import HabitatClientSource
from infrastructure.mqtt.listener import SensorListener
from app.api.routes import setup_routes
from domain.scenarios.scenario_manager import ScenarioManager
from domain.profiles.profile_manager import ProfileManager
from domain.house_states.house import House
from domain.house_states.states import get_state_for_mode
from domain.integrations.smart_home_adapter import (
    PhilipsHueAdapter,
    NestAdapter,
    GenericAdapter,
)
from domain.integrations.cache_proxy import CacheProxy
from domain.integrations.decorators import LoggingDecorator
from domain.dashboard.dashboard_facade import DashboardFacade
from infrastructure.db.sqlalchemy_models import DeviceRecord
from infrastructure.db.sqlalchemy_session import get_default_session_factory
from infrastructure.db.unit_of_work import SQLAlchemyUnitOfWork
from infrastructure.di.container import build_default_container
from app.core.provided_auth import get_current_user, require_minimum_role, User
from application.services.auth_service import AuthService
from infrastructure.auth.service_locator import build_default_service_locator

# ============================================================================
# CRÉATION APP
# ============================================================================

app = FastAPI(title="Habitat Intelligent")
templates = Jinja2Templates(directory="templates")

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
    limit: int = Query(100, ge=1, le=1000),
):
    return _history.get_filtered_history(location, sensor_type, start_date, end_date, limit)


@app.get("/api/stats/hourly")
def get_hourly_stats(
    location: Optional[str] = Query(None),
    sensor_type: str = Query("temperature"),
    date: Optional[str] = Query(None),
):
    return _stats_advanced.calculate_hourly_stats(location, sensor_type, date)


@app.get("/api/alerts/config")
def get_alert_config():
    return _alerts.get_config()


@app.post("/api/alerts/config")
def update_alert_config(config: AlertConfigUpdate):
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
    alerts = _alerts.generate_alerts(LOCATIONS)
    return {"count": len(alerts), "alerts": alerts}


# ============================================================================
# ITERATION 4 - Patterns Comportementaux (Observer, Strategy, State)
# ============================================================================

_scenario_manager = ScenarioManager()
_profile_manager = ProfileManager()
_house = House()


@app.post("/api/scenarios")
def create_scenario(data: dict):
    """Cree un scenario automatise (Observer)"""
    try:
        scenario = _scenario_manager.create_scenario(
            name=data["name"],
            conditions=data.get("conditions", []),
            actions=data.get("actions", []),
            description=data.get("description", ""),
        )
        return {"status": "ok", "scenario": scenario.to_dict()}
    except (KeyError, ValueError) as e:
        return {"status": "error", "message": str(e)}


@app.get("/api/scenarios")
def list_scenarios():
    """Liste tous les scenarios"""
    scenarios = _scenario_manager.get_all_scenarios()
    return {"count": len(scenarios), "scenarios": [s.to_dict() for s in scenarios]}


@app.post("/api/scenarios/{id}/execute")
def execute_scenario(id: str):
    """Execute un scenario manuellement"""
    result = _scenario_manager.execute_scenario(id)
    if result:
        return {"status": "ok", "result": result}
    return {"status": "error", "message": "Scenario not found"}


@app.get("/api/scenarios/{id}/conditions")
def get_scenario_conditions(id: str):
    """Retourne les conditions d'un scenario"""
    scenario = _scenario_manager.get_scenario(id)
    if scenario:
        return {"scenario_id": id, "conditions": [c.to_dict() for c in scenario.conditions]}
    return {"status": "error", "message": "Scenario not found"}


@app.get("/api/scenarios/{id}")
def get_scenario(id: str):
    """Retourne un scenario par ID"""
    scenario = _scenario_manager.get_scenario(id)
    if scenario:
        return {"status": "ok", "scenario": scenario.to_dict()}
    return {"status": "error", "message": "Scenario not found"}


@app.put("/api/scenarios/{id}/activate")
def toggle_scenario(id: str, data: dict = None):
    """Active ou desactive un scenario"""
    active = (data or {}).get("active", True)
    if active:
        ok = _scenario_manager.activate_scenario(id)
    else:
        ok = _scenario_manager.deactivate_scenario(id)
    if ok:
        return {"status": "ok", "scenario_id": id, "active": active}
    return {"status": "error", "message": "Scenario not found"}


@app.delete("/api/scenarios/{id}")
def delete_scenario(id: str):
    """Supprime un scenario"""
    if _scenario_manager.delete_scenario(id):
        return {"status": "ok", "message": f"Scenario {id} deleted"}
    return {"status": "error", "message": "Scenario not found"}


@app.get("/api/profiles/current")
def get_current_profile():
    """Retourne le profil actif"""
    profile = _profile_manager.get_current_profile()
    if profile:
        strategy = _profile_manager.get_current_strategy()
        return {"profile": profile.to_dict(), "strategy": strategy.apply() if strategy else None}
    return {"profile": None, "strategy": None}


@app.post("/api/profiles")
def create_profile(data: dict):
    """Cree un profil utilisateur (Strategy)"""
    try:
        profile = _profile_manager.create_profile(
            name=data["name"],
            strategy_type=data["strategy_type"],
            settings=data.get("settings", {}),
        )
        return {"status": "ok", "profile": profile.to_dict()}
    except (KeyError, ValueError) as e:
        return {"status": "error", "message": str(e)}


@app.get("/api/profiles")
def list_profiles():
    """Liste tous les profils"""
    profiles = _profile_manager.get_all_profiles()
    return {"count": len(profiles), "profiles": [p.to_dict() for p in profiles]}


@app.post("/api/profiles/{id}/activate")
def activate_profile(id: str):
    """Active un profil et applique sa strategie"""
    if _profile_manager.activate_profile(id):
        profile = _profile_manager.get_profile(id)
        strategy = _profile_manager.get_current_strategy()
        return {
            "status": "ok",
            "profile": profile.to_dict(),
            "strategy_applied": strategy.apply() if strategy else None,
        }
    return {"status": "error", "message": "Profile not found"}


@app.get("/api/house/mode")
def get_house_mode():
    """Retourne le mode actuel de la maison (State)"""
    return {"mode": _house.get_current_mode(), "config": _house.get_mode_config()}


@app.put("/api/house/mode")
def set_house_mode(data: dict):
    """Change le mode de la maison manuellement"""
    try:
        state = get_state_for_mode(data.get("mode", ""))
        _house.set_state(state)
        return {
            "status": "ok",
            "mode": _house.get_current_mode(),
            "config": _house.get_mode_config(),
        }
    except ValueError as e:
        return {"status": "error", "message": str(e)}


@app.get("/api/house/mode/history")
def get_house_mode_history():
    """Retourne l'historique des changements de mode"""
    history = _house.get_mode_history()
    return {"count": len(history), "history": history}


# ============================================================================
# ITERATION 5 - Patterns Structurels (Adapter, Proxy, Facade, Decorator)
# ============================================================================

_hue_adapter = LoggingDecorator(CacheProxy(PhilipsHueAdapter(), ttl=30))
_nest_adapter = LoggingDecorator(CacheProxy(NestAdapter(), ttl=30))
_generic_adapter = LoggingDecorator(CacheProxy(GenericAdapter(), ttl=30))

_dashboard_facade = DashboardFacade(
    scenario_manager=_scenario_manager,
    profile_manager=_profile_manager,
    house=_house,
)
_dashboard_facade.register_adapter(PhilipsHueAdapter())
_dashboard_facade.register_adapter(NestAdapter())
_dashboard_facade.register_adapter(GenericAdapter())


@app.get("/api/integrations/philips-hue")
def get_philips_hue_integration():
    """Retourne le statut et les appareils Philips Hue (Adapter + Proxy)"""
    return {
        "status": "ok",
        "integration": _hue_adapter.get_status(),
        "devices": _hue_adapter.get_devices(),
    }


@app.get("/api/integrations/nest")
def get_nest_integration():
    """Retourne le statut et les appareils Nest (Adapter + Proxy)"""
    return {
        "status": "ok",
        "integration": _nest_adapter.get_status(),
        "devices": _nest_adapter.get_devices(),
    }


@app.get("/api/integrations/generic")
def get_generic_integration():
    """Retourne le statut et les appareils generiques (Adapter + Proxy)"""
    return {
        "status": "ok",
        "integration": _generic_adapter.get_status(),
        "devices": _generic_adapter.get_devices(),
    }


@app.get("/api/dashboard/summary")
def get_dashboard_summary():
    """Retourne le resume unifie de la maison (Facade)"""
    return {"status": "ok", "summary": _dashboard_facade.get_summary()}


@app.get("/api/dashboard/widgets")
def get_dashboard_widgets():
    """Retourne les widgets du dashboard (Facade)"""
    widgets = _dashboard_facade.get_widgets()
    return {"status": "ok", "count": len(widgets), "widgets": widgets}


# ============================================================================
# ITERATION 6 - Repository + Unit of Work + DI Container
# ============================================================================

_session_factory = get_default_session_factory()
_di_container = build_default_container()


@app.post("/api/devices/batch")
def create_devices_batch(devices: List[dict]):
    """
    Cree plusieurs devices en une seule transaction (Unit of Work).
    Si un device est invalide, toute la transaction est annulee.
    """
    created = []
    with SQLAlchemyUnitOfWork(_session_factory) as uow:
        try:
            for data in devices:
                if not data.get("device_id") or not data.get("name"):
                    uow.rollback()
                    return {
                        "status": "error",
                        "message": "Chaque device doit avoir device_id et name",
                        "rolled_back": True,
                    }
                record = DeviceRecord(
                    device_id=data["device_id"],
                    name=data["name"],
                    room_name=data.get("room_name", ""),
                    device_type=data.get("device_type", ""),
                    manufacturer=data.get("manufacturer", ""),
                    status=data.get("status", "active"),
                )
                uow.devices.save(record)
                created.append(data["device_id"])
            uow.commit()
        except Exception as e:
            uow.rollback()
            return {"status": "error", "message": str(e), "rolled_back": True}
    return {"status": "ok", "created": len(created), "device_ids": created}


@app.get("/api/db/devices")
def list_stored_devices():
    """Liste les devices persistes via SQLAlchemy (Iteration 6)"""
    with SQLAlchemyUnitOfWork(_session_factory) as uow:
        devices = uow.devices.find_all()
        return {"devices": [d.to_dict() for d in devices]}


@app.delete("/api/db/devices/{device_id}")
def delete_stored_device(device_id: str):
    """Supprime un device persiste via SQLAlchemy (Iteration 6)"""
    with SQLAlchemyUnitOfWork(_session_factory) as uow:
        deleted = uow.devices.delete(device_id)
        if deleted:
            uow.commit()
            return {"status": "ok", "message": f"Device {device_id} supprime"}
        return {"status": "error", "message": "Device non trouve"}


@app.put("/api/db/devices/{device_id}")
def update_stored_device(device_id: str, data: dict):
    """Met a jour un device persiste via SQLAlchemy (Iteration 6)"""
    with SQLAlchemyUnitOfWork(_session_factory) as uow:
        device = uow.devices.find_by_id(device_id)
        if not device:
            return {"status": "error", "message": "Device non trouve"}
        if "name" in data:
            device.name = data["name"]
        if "room_name" in data:
            device.room_name = data["room_name"]
        if "device_type" in data:
            device.device_type = data["device_type"]
        if "manufacturer" in data:
            device.manufacturer = data["manufacturer"]
        uow.commit()
        return {"status": "ok", "device": device.to_dict()}


@app.get("/devices", response_class=HTMLResponse)
def devices_list_page(request: Request):
    """Page CRUD des devices (Iteration 6 - bonus)"""
    return templates.TemplateResponse("devices.html", {"request": request})


@app.get("/devices/new", response_class=HTMLResponse)
def devices_new_page(request: Request):
    """Formulaire creation d'un device (Iteration 6 - bonus)"""
    return templates.TemplateResponse("devices_new.html", {"request": request})


@app.get("/devices/import", response_class=HTMLResponse)
def devices_import_page(request: Request):
    """Interface import batch de devices (Iteration 6 - bonus)"""
    return templates.TemplateResponse("devices_import.html", {"request": request})


@app.post("/api/transactions/rollback-test")
def test_transaction_rollback(data: dict = None):
    """
    Demonstration du mecanisme de rollback.
    Insere des donnees puis provoque un rollback si force_rollback=true.
    """
    data = data or {}
    force_rollback = data.get("force_rollback", True)
    test_devices = data.get("devices", [
        {"device_id": "test-rollback-1", "name": "Test Device 1"},
        {"device_id": "test-rollback-2", "name": "Test Device 2"},
    ])

    inserted = []
    with SQLAlchemyUnitOfWork(_session_factory) as uow:
        for device_data in test_devices:
            record = DeviceRecord(
                device_id=device_data.get("device_id", ""),
                name=device_data.get("name", ""),
            )
            uow.devices.save(record)
            inserted.append(device_data.get("device_id", ""))

        if force_rollback:
            uow.rollback()
            return {
                "status": "ok",
                "action": "rollback",
                "message": "Transaction annulee avec succes",
                "attempted_inserts": inserted,
                "persisted": False,
            }
        uow.commit()

    return {
        "status": "ok",
        "action": "commit",
        "message": "Transaction validee",
        "persisted_devices": inserted,
        "persisted": True,
    }


# ============================================================================
# ITERATION 7 - Auth + RBAC + Repository per User + Service Locator
# ============================================================================

_auth_service = AuthService()
_service_locator = build_default_service_locator()


@app.post("/api/auth/register")
def auth_register(data: dict):
    """Enregistre un nouvel utilisateur."""
    try:
        user = _auth_service.register(
            username=data["username"],
            password=data["password"],
            role=data.get("role", "user"),
        )
        return {"status": "ok", "user": user.to_dict()}
    except (KeyError, ValueError) as e:
        return {"status": "error", "message": str(e)}


@app.post("/api/auth/login")
def auth_login(data: dict):
    """Authentifie un utilisateur et retourne un token."""
    token = _auth_service.login(
        username=data.get("username", ""),
        password=data.get("password", ""),
    )
    if token is None:
        return {"status": "error", "message": "Identifiants invalides"}
    user = _auth_service.get_by_token(token)
    return {"status": "ok", "token": token, "user": user.to_dict()}


@app.get("/api/auth/me")
def auth_me(current_user: User = Depends(get_current_user)):
    """Retourne le profil de l'utilisateur authentifie."""
    user_account = _auth_service.get_by_token(
        current_user.id if current_user.id.startswith("token_") else None
    )
    return {
        "user": {
            "id": current_user.id,
            "role": current_user.role,
            "permissions": current_user.permissions,
            "username": user_account.username if user_account else current_user.id,
        }
    }


@app.get("/api/auth/users")
def list_users(current_user: User = Depends(get_current_user)):
    """Liste tous les utilisateurs (admin only)."""
    require_minimum_role(current_user, "admin")
    users = _auth_service.get_all_users()
    return {"count": len(users), "users": [u.to_dict() for u in users]}


@app.get("/api/users/{id}/devices")
def get_user_devices(id: str, current_user: User = Depends(get_current_user)):
    """Retourne les devices d'un utilisateur (isolation applicative)."""
    if current_user.id != id:
        require_minimum_role(current_user, "admin")
    repo = _service_locator.resolve_for_user("user_device_repository", id)
    return {"user_id": id, "devices": repo.get_all(), "count": repo.count()}


@app.post("/api/users/{id}/devices")
def add_user_device(
    id: str,
    data: dict,
    current_user: User = Depends(get_current_user),
):
    """Ajoute un device pour un utilisateur."""
    if current_user.id != id:
        require_minimum_role(current_user, "admin")
    repo = _service_locator.resolve_for_user("user_device_repository", id)
    device = repo.add_device(data.get("device_id", ""), data)
    return {"status": "ok", "device": device}


@app.get("/api/users/{id}/permissions")
def get_user_permissions(id: str, current_user: User = Depends(get_current_user)):
    """Retourne les permissions d'un utilisateur."""
    if current_user.id != id:
        require_minimum_role(current_user, "admin")
    permissions = _auth_service.get_user_permissions(id)
    if not permissions:
        permissions = current_user.permissions if current_user.id == id else []
    return {"user_id": id, "permissions": permissions}


# Frontend routes (bonus iteration 7)
@app.get("/login", response_class=HTMLResponse)
def login_page(request: Request):
    """Page de connexion (Iteration 7 - bonus)"""
    return templates.TemplateResponse("login.html", {"request": request})


@app.get("/register", response_class=HTMLResponse)
def register_page(request: Request):
    """Page d'inscription (Iteration 7 - bonus)"""
    return templates.TemplateResponse("register.html", {"request": request})


@app.get("/users", response_class=HTMLResponse)
def users_page(request: Request):
    """Page de gestion des utilisateurs (Iteration 7 - bonus)"""
    return templates.TemplateResponse("users.html", {"request": request})


@app.get("/users/permissions", response_class=HTMLResponse)
def users_permissions_page(request: Request):
    """Page des roles et permissions (Iteration 7 - bonus)"""
    return templates.TemplateResponse("users_permissions.html", {"request": request})


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
