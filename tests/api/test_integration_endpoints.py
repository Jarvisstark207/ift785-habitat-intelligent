"""Tests API - Endpoints integrations tierces et dashboard unifie"""

import pytest
from fastapi.testclient import TestClient

from app import app


@pytest.fixture(scope="module")
def client():
    return TestClient(app)


class TestIntegrationEndpoints:

    def test_get_philips_hue_retourne_200(self, client):
        """GET /api/integrations/philips-hue retourne 200"""
        response = client.get("/api/integrations/philips-hue")
        assert response.status_code == 200

    def test_get_philips_hue_structure(self, client):
        """GET /api/integrations/philips-hue retourne la bonne structure"""
        response = client.get("/api/integrations/philips-hue")
        data = response.json()
        assert data["status"] == "ok"
        assert "integration" in data
        assert "devices" in data

    def test_get_philips_hue_adapter_name(self, client):
        """L'integration Hue a le bon nom"""
        response = client.get("/api/integrations/philips-hue")
        assert response.json()["integration"]["adapter"] == "philips-hue"

    def test_get_nest_retourne_200(self, client):
        """GET /api/integrations/nest retourne 200"""
        response = client.get("/api/integrations/nest")
        assert response.status_code == 200

    def test_get_nest_structure(self, client):
        data = client.get("/api/integrations/nest").json()
        assert data["status"] == "ok"
        assert "integration" in data
        assert "devices" in data

    def test_get_nest_adapter_name(self, client):
        data = client.get("/api/integrations/nest").json()
        assert data["integration"]["adapter"] == "nest"

    def test_get_generic_retourne_200(self, client):
        """GET /api/integrations/generic retourne 200"""
        response = client.get("/api/integrations/generic")
        assert response.status_code == 200

    def test_get_generic_structure(self, client):
        data = client.get("/api/integrations/generic").json()
        assert data["status"] == "ok"
        assert "devices" in data


class TestDashboardEndpoints:

    def test_get_summary_retourne_200(self, client):
        """GET /api/dashboard/summary retourne 200"""
        response = client.get("/api/dashboard/summary")
        assert response.status_code == 200

    def test_get_summary_structure(self, client):
        """GET /api/dashboard/summary retourne la bonne structure"""
        data = client.get("/api/dashboard/summary").json()
        assert data["status"] == "ok"
        assert "summary" in data
        summary = data["summary"]
        assert "house_mode" in summary
        assert "active_profile" in summary
        assert "alerts" in summary
        assert "scenarios" in summary
        assert "integrations" in summary

    def test_get_widgets_retourne_200(self, client):
        """GET /api/dashboard/widgets retourne 200"""
        response = client.get("/api/dashboard/widgets")
        assert response.status_code == 200

    def test_get_widgets_structure(self, client):
        """GET /api/dashboard/widgets retourne la bonne structure"""
        data = client.get("/api/dashboard/widgets").json()
        assert data["status"] == "ok"
        assert "widgets" in data
        assert "count" in data
        assert data["count"] == len(data["widgets"])

    def test_get_widgets_contient_4_elements(self, client):
        data = client.get("/api/dashboard/widgets").json()
        assert data["count"] == 4

    def test_summary_integrations_presentes(self, client):
        """Le summary contient les integrations enregistrees"""
        data = client.get("/api/dashboard/summary").json()
        integrations = data["summary"]["integrations"]
        assert len(integrations) >= 1
