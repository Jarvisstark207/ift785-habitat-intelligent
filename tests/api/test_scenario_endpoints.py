"""Tests API - Endpoints scenarios, profils et modes maison"""

import pytest
from fastapi.testclient import TestClient

from app import app


@pytest.fixture(scope="module")
def client():
    return TestClient(app)


@pytest.fixture
def scenario_payload():
    return {
        "name": "Test refroidissement",
        "description": "Ventilateur si temperature > 26",
        "conditions": [
            {"trigger_type": "temperature", "operator": ">", "value": 26.0}
        ],
        "actions": [
            {"device_id": "fan_01", "action": "turn_on",
             "parameters": {"speed": "medium"}}
        ],
    }


# ---------------------------------------------------------------------------
# Tests endpoints /api/scenarios
# ---------------------------------------------------------------------------

class TestScenarioEndpoints:

    def test_post_scenario_retourne_200(self, client, scenario_payload):
        """POST /api/scenarios cree un scenario"""
        response = client.post("/api/scenarios", json=scenario_payload)
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "ok"
        assert "scenario" in data

    def test_get_scenarios_retourne_liste(self, client, scenario_payload):
        """GET /api/scenarios retourne une liste de scenarios"""
        client.post("/api/scenarios", json=scenario_payload)
        response = client.get("/api/scenarios")
        assert response.status_code == 200
        data = response.json()
        assert "scenarios" in data
        assert "count" in data

    def test_post_scenario_champs_obligatoires(self, client):
        """POST /api/scenarios echoue sans le champ 'name'"""
        response = client.post("/api/scenarios", json={"conditions": [], "actions": []})
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "error"

    def test_execute_scenario(self, client, scenario_payload):
        """POST /api/scenarios/{id}/execute execute le scenario"""
        create_resp = client.post("/api/scenarios", json=scenario_payload)
        scenario_id = create_resp.json()["scenario"]["id"]
        exec_resp = client.post(f"/api/scenarios/{scenario_id}/execute")
        assert exec_resp.status_code == 200
        data = exec_resp.json()
        assert data["status"] == "ok"
        assert "result" in data

    def test_get_conditions_scenario(self, client, scenario_payload):
        """GET /api/scenarios/{id}/conditions retourne les conditions"""
        create_resp = client.post("/api/scenarios", json=scenario_payload)
        scenario_id = create_resp.json()["scenario"]["id"]
        cond_resp = client.get(f"/api/scenarios/{scenario_id}/conditions")
        assert cond_resp.status_code == 200
        data = cond_resp.json()
        assert "conditions" in data
        assert len(data["conditions"]) == 1

    def test_execute_scenario_inexistant(self, client):
        """POST /api/scenarios/{id}/execute avec ID inexistant"""
        response = client.post("/api/scenarios/id-fantome/execute")
        assert response.status_code == 200
        assert response.json()["status"] == "error"

    def test_delete_scenario(self, client, scenario_payload):
        """DELETE /api/scenarios/{id} supprime le scenario"""
        create_resp = client.post("/api/scenarios", json=scenario_payload)
        scenario_id = create_resp.json()["scenario"]["id"]
        del_resp = client.delete(f"/api/scenarios/{scenario_id}")
        assert del_resp.status_code == 200
        assert del_resp.json()["status"] == "ok"

    def test_get_conditions_inexistant(self, client):
        """GET /api/scenarios/{id}/conditions avec ID inexistant"""
        response = client.get("/api/scenarios/id-fantome/conditions")
        assert response.status_code == 200
        assert response.json()["status"] == "error"


# ---------------------------------------------------------------------------
# Tests endpoints /api/profiles
# ---------------------------------------------------------------------------

class TestProfileEndpoints:

    def test_get_profiles_retourne_trois_defaut(self, client):
        """GET /api/profiles retourne au moins 3 profils par defaut"""
        response = client.get("/api/profiles")
        assert response.status_code == 200
        data = response.json()
        assert data["count"] >= 3

    def test_post_profile_personnalise(self, client):
        """POST /api/profiles cree un profil personnalise"""
        payload = {
            "name": "Profil test",
            "strategy_type": "comfort",
            "settings": {"custom_temp": 22.0},
        }
        response = client.post("/api/profiles", json=payload)
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "ok"
        assert data["profile"]["name"] == "Profil test"

    def test_activate_profile(self, client):
        """POST /api/profiles/{id}/activate active le profil"""
        profiles_resp = client.get("/api/profiles")
        profiles = profiles_resp.json()["profiles"]
        profile_id = profiles[0]["id"]
        response = client.post(f"/api/profiles/{profile_id}/activate")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "ok"

    def test_activate_profile_inexistant(self, client):
        """POST /api/profiles/{id}/activate avec ID inexistant"""
        response = client.post("/api/profiles/id-fantome/activate")
        assert response.status_code == 200
        assert response.json()["status"] == "error"

    def test_get_current_profile_apres_activation(self, client):
        """GET /api/profiles/current retourne le profil active"""
        profiles_resp = client.get("/api/profiles")
        profile_id = profiles_resp.json()["profiles"][0]["id"]
        client.post(f"/api/profiles/{profile_id}/activate")
        response = client.get("/api/profiles/current")
        assert response.status_code == 200
        data = response.json()
        assert data["profile"] is not None


# ---------------------------------------------------------------------------
# Tests endpoints /api/house/mode
# ---------------------------------------------------------------------------

class TestHouseModeEndpoints:

    def test_get_house_mode_retourne_mode(self, client):
        """GET /api/house/mode retourne le mode actuel"""
        response = client.get("/api/house/mode")
        assert response.status_code == 200
        data = response.json()
        assert "mode" in data
        assert "config" in data

    def test_set_house_mode_nuit(self, client):
        """PUT /api/house/mode change le mode en nuit"""
        response = client.put("/api/house/mode", json={"mode": "nuit"})
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "ok"
        assert data["mode"] == "nuit"

    def test_set_house_mode_vacances(self, client):
        """PUT /api/house/mode change le mode en vacances"""
        response = client.put("/api/house/mode", json={"mode": "vacances"})
        assert response.status_code == 200
        assert response.json()["mode"] == "vacances"

    def test_set_house_mode_inconnu(self, client):
        """PUT /api/house/mode avec mode inconnu retourne une erreur"""
        response = client.put("/api/house/mode", json={"mode": "mode_inexistant"})
        assert response.status_code == 200
        assert response.json()["status"] == "error"

    def test_get_house_mode_history(self, client):
        """GET /api/house/mode/history retourne l'historique"""
        client.put("/api/house/mode", json={"mode": "domicile"})
        response = client.get("/api/house/mode/history")
        assert response.status_code == 200
        data = response.json()
        assert "history" in data
        assert "count" in data
