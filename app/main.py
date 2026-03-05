#!/usr/bin/env python3
"""
Application Habitat Intelligent - Architecture Clean
Refactorée selon principes POO et SOLID
"""

import threading
import uvicorn
from fastapi import FastAPI

from app.api.routes import setup_routes
from application.services.dashboard_service import DashboardService
from application.services.stats_service import StatsService
from application.services.alert_service import AlertService
from application.use_cases.ingest_sensor_reading import IngestSensorReading
from infrastructure.db.sqlite_sensor_repo import SQLiteSensorRepository
from infrastructure.mqtt.habitat_client_source import HabitatClientSource
from infrastructure.mqtt.listener import SensorListener


def create_app() -> FastAPI:
    """Factory pour créer l'application FastAPI avec dépendances"""

    # Créer repository
    repository = SQLiteSensorRepository()

    # Créer services
    stats_service = StatsService(repository)
    alert_service = AlertService(stats_service)
    dashboard_service = DashboardService(
        repository,
        stats_service,
        alert_service
    )

    # Créer app FastAPI
    app = FastAPI(title="Habitat Intelligent")

    # Configurer routes
    setup_routes(app, dashboard_service)

    return app, repository


def start_sensor_listener(repository: SQLiteSensorRepository) -> None:
    """Démarre le thread d'écoute des capteurs"""

    # Créer source de données
    sensor_source = HabitatClientSource()

    # Créer use case d'ingestion
    ingest_use_case = IngestSensorReading(repository)

    # Créer et démarrer listener
    listener = SensorListener(sensor_source, ingest_use_case)

    # Lancer dans un thread
    mqtt_thread = threading.Thread(
        target=listener.start_listening,
        daemon=True
    )
    mqtt_thread.start()

    print("Thread collecte demarre")


def main() -> None:
    print("=" * 70)
    print("HABITAT INTELLIGENT - DEMARRAGE")
    print("=" * 70)

    app, repository = create_app()
    start_sensor_listener(repository)

    print("Serveur web: http://localhost:8000")
    print("=" * 70)

    uvicorn.run(app, host="0.0.0.0", port=8000, log_level="warning")


if __name__ == "__main__":
    main()
