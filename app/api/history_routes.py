"""Routes pour l'historique des données"""
from fastapi import APIRouter, Query
from typing import Optional
from datetime import datetime
from application.services.history_service import HistoryService
from infrastructure.db.sqlite_sensor_repo import SQLiteSensorRepository

router = APIRouter(prefix="/api/data", tags=["history"])

# Dépendances
_repo = SQLiteSensorRepository()
_history_service = HistoryService(_repo)


@router.get("/history")
def get_history(
    location: Optional[str] = Query(None, description="Filter by location"),
    sensor_type: Optional[str] = Query(None, description="Filter by sensor type"),
    start_date: Optional[str] = Query(None, description="Start date (ISO format)"),
    end_date: Optional[str] = Query(None, description="End date (ISO format)"),
    limit: int = Query(100, ge=1, le=1000, description="Max results")
):
    """Récupère l'historique filtré des lectures"""
    return _history_service.get_filtered_history(
        location=location,
        sensor_type=sensor_type,
        start_date=start_date,
        end_date=end_date,
        limit=limit
    )