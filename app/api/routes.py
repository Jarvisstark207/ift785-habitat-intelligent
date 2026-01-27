from fastapi import FastAPI
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from starlette.requests import Request
from application.services.dashboard_service import DashboardService
from config import LOCATIONS


def setup_routes(app: FastAPI, dashboard_service: DashboardService) -> None:
    """Configure les routes FastAPI"""

    # Fichiers statiques et templates
    app.mount("/static", StaticFiles(directory="static"), name="static")
    templates = Jinja2Templates(directory="templates")

    @app.get("/api/data")
    def get_dashboard_data():
        """API JSON pour dashboard"""
        return dashboard_service.get_dashboard_data(LOCATIONS)

    @app.get("/", response_class=HTMLResponse)
    def homepage(request: Request):
        """Page HTML dashboard"""
        return templates.TemplateResponse("index.html", {"request": request})
