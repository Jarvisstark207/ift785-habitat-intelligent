"""Tests d'intégration pour les API des devices"""

import pytest
from fastapi.testclient import TestClient

from app import app
from domain.models.device_registry import DeviceRegistry


@pytest.fixture(autouse=True)
def clear_registry():
    """Nettoie le registre avant et après chaque test"""
    registry = DeviceRegistry.get_instance()
    registry.clear()
    yield
    registry.clear()


client = TestClient(app)


class TestDeviceAPI:
    """Tests pour les endpoints d'API des devices"""

    def test_build_device_endpoint(self):
        """Teste l'endpoint POST /api/devices/build"""
        payload = {
            "device_id": "light_1",
            "name": "Living Room Light",
            "room_name": "Living Room",
            "device_type": "light",
            "brightness": 80,
            "color": "warm",
        }
        response = client.post("/api/devices/build", json=payload)
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "ok"
        assert data["device"]["device_id"] == "light_1"
        assert data["device"]["brightness"] == 80

    def test_build_device_missing_required_field(self):
        """Teste l'endpoint avec champ obligatoire manquant"""
        payload = {
            "device_id": "light_1",
            "name": "Light",
        }
        response = client.post("/api/devices/build", json=payload)
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "error"

    def test_list_devices_empty(self):
        """Teste l'endpoint GET /api/devices quand vide"""
        response = client.get("/api/devices")
        assert response.status_code == 200
        data = response.json()
        assert data["count"] == 0
        assert data["devices"] == []

    def test_list_devices(self):
        """Teste l'endpoint GET /api/devices"""
        # Créer quelques devices
        payload1 = {
            "device_id": "light_1",
            "name": "Light",
            "room_name": "Room",
            "device_type": "light",
        }
        payload2 = {
            "device_id": "thermo_1",
            "name": "Thermostat",
            "room_name": "Room",
            "device_type": "thermostat",
        }
        client.post("/api/devices/build", json=payload1)
        client.post("/api/devices/build", json=payload2)

        response = client.get("/api/devices")
        assert response.status_code == 200
        data = response.json()
        assert data["count"] == 2

    def test_get_device_endpoint(self):
        """Teste l'endpoint GET /api/devices/{device_id}"""
        payload = {
            "device_id": "light_1",
            "name": "Light",
            "room_name": "Room",
            "device_type": "light",
        }
        client.post("/api/devices/build", json=payload)

        response = client.get("/api/devices/light_1")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "ok"
        assert data["device"]["device_id"] == "light_1"

    def test_get_nonexistent_device(self):
        """Teste la récupération d'un device inexistant"""
        response = client.get("/api/devices/nonexistent")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "error"

    def test_get_devices_by_type(self):
        """Teste l'endpoint GET /api/devices/type/{device_type}"""
        # Créer plusieurs lights
        for i in range(3):
            payload = {
                "device_id": f"light_{i}",
                "name": f"Light {i}",
                "room_name": "Room",
                "device_type": "light",
            }
            client.post("/api/devices/build", json=payload)

        # Créer un thermostat
        payload = {
            "device_id": "thermo_1",
            "name": "Thermostat",
            "room_name": "Room",
            "device_type": "thermostat",
        }
        client.post("/api/devices/build", json=payload)

        response = client.get("/api/devices/type/light")
        assert response.status_code == 200
        data = response.json()
        assert data["count"] == 3
        assert data["device_type"] == "light"

    def test_get_devices_by_room(self):
        """Teste l'endpoint GET /api/devices/room/{room_name}"""
        payload1 = {
            "device_id": "light_1",
            "name": "Light",
            "room_name": "Living Room",
            "device_type": "light",
        }
        payload2 = {
            "device_id": "light_2",
            "name": "Light",
            "room_name": "Bedroom",
            "device_type": "light",
        }
        client.post("/api/devices/build", json=payload1)
        client.post("/api/devices/build", json=payload2)

        response = client.get("/api/devices/room/Living%20Room")
        assert response.status_code == 200
        data = response.json()
        assert data["count"] == 1
        assert data["room"] == "Living Room"

    def test_get_devices_by_manufacturer(self):
        """Teste l'endpoint GET /api/devices/manufacturer/{manufacturer}"""
        payload1 = {
            "device_id": "light_1",
            "name": "Light",
            "room_name": "Room",
            "device_type": "light",
            "manufacturer": "philips",
        }
        payload2 = {
            "device_id": "light_2",
            "name": "Light",
            "room_name": "Room",
            "device_type": "light",
            "manufacturer": "nest",
        }
        client.post("/api/devices/build", json=payload1)
        client.post("/api/devices/build", json=payload2)

        response = client.get("/api/devices/manufacturer/Philips")
        assert response.status_code == 200
        data = response.json()
        assert data["count"] == 1
        assert data["manufacturer"] == "Philips"

    def test_delete_device(self):
        """Teste l'endpoint DELETE /api/devices/{device_id}"""
        payload = {
            "device_id": "light_1",
            "name": "Light",
            "room_name": "Room",
            "device_type": "light",
        }
        client.post("/api/devices/build", json=payload)

        response = client.delete("/api/devices/light_1")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "ok"

        # Vérifier que le device est supprimé
        response = client.get("/api/devices/light_1")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "error"

    def test_delete_nonexistent_device(self):
        """Teste la suppression d'un device inexistant"""
        response = client.delete("/api/devices/nonexistent")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "error"

    def test_build_thermostat(self):
        """Teste la construction d'un thermostat"""
        payload = {
            "device_id": "thermo_1",
            "name": "Living Room Thermostat",
            "room_name": "Living Room",
            "device_type": "thermostat",
            "temperature": 22.0,
            "target_temperature": 21.0,
            "mode": "cool",
        }
        response = client.post("/api/devices/build", json=payload)
        assert response.status_code == 200
        data = response.json()
        assert data["device"]["type"] == "thermostat"
        assert data["device"]["temperature"] == 22.0

    def test_build_co2_sensor(self):
        """Teste la construction d'un capteur CO2"""
        payload = {
            "device_id": "co2_1",
            "name": "Office CO2 Sensor",
            "room_name": "Office",
            "device_type": "co2_sensor",
            "ppm": 800.0,
            "alarm_threshold": 1200.0,
        }
        response = client.post("/api/devices/build", json=payload)
        assert response.status_code == 200
        data = response.json()
        assert data["device"]["type"] == "co2_sensor"
        assert data["device"]["ppm"] == 800.0

    def test_build_motion_sensor(self):
        """Teste la construction d'un capteur de mouvement"""
        payload = {
            "device_id": "motion_1",
            "name": "Hallway Motion Sensor",
            "room_name": "Hallway",
            "device_type": "motion_sensor",
            "sensitivity": 8,
        }
        response = client.post("/api/devices/build", json=payload)
        assert response.status_code == 200
        data = response.json()
        assert data["device"]["type"] == "motion_sensor"
        assert data["device"]["sensitivity"] == 8

    def test_build_with_different_manufacturers(self):
        """Teste la construction avec différents fabricants"""
        manufacturers = ["philips", "nest", "generic"]
        for i, manufacturer in enumerate(manufacturers):
            payload = {
                "device_id": f"light_{i}",
                "name": f"Light {i}",
                "room_name": "Room",
                "device_type": "light",
                "manufacturer": manufacturer,
            }
            response = client.post("/api/devices/build", json=payload)
            assert response.status_code == 200
            data = response.json()
            # Le fabricant devrait être avec majuscule
            assert manufacturer.lower() in data["device"]["manufacturer"].lower()
    def test_update_device(self):
        """Teste la mise à jour d'un device"""
        payload = {
            "device_id": "light_1",
            "name": "Original Light",
            "room_name": "Room",
            "device_type": "light",
            "brightness": 50,
        }
        client.post("/api/devices/build", json=payload)

        # Mettre à jour
        update_payload = {
            "name": "Updated Light",
            "brightness": 80,
        }
        response = client.put("/api/devices/light_1", json=update_payload)
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "ok"
        assert data["device"]["brightness"] == 80

    def test_update_nonexistent_device(self):
        """Teste la mise à jour d'un device qui n'existe pas"""
        update_payload = {"name": "Updated"}
        response = client.put("/api/devices/nonexistent", json=update_payload)
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "error"

    def test_list_devices_paginated(self):
        """Teste la pagination des devices"""
        # Créer 15 devices
        for i in range(15):
            payload = {
                "device_id": f"light_{i}",
                "name": f"Light {i}",
                "room_name": "Room",
                "device_type": "light",
            }
            client.post("/api/devices/build", json=payload)

        # Première page
        response = client.get("/api/devices/paginated/list?skip=0&limit=10")
        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 15
        assert data["count"] == 10
        assert data["skip"] == 0
        assert data["limit"] == 10

        # Deuxième page
        response = client.get("/api/devices/paginated/list?skip=10&limit=10")
        assert response.status_code == 200
        data = response.json()
        assert data["count"] == 5

    def test_search_devices_by_type(self):
        """Teste la recherche filtrée par type"""
        # Créer des devices de différents types
        for i in range(3):
            payload = {
                "device_id": f"light_{i}",
                "name": f"Light {i}",
                "room_name": "Room",
                "device_type": "light",
            }
            client.post("/api/devices/build", json=payload)

        payload = {
            "device_id": "thermo_1",
            "name": "Thermostat",
            "room_name": "Room",
            "device_type": "thermostat",
        }
        client.post("/api/devices/build", json=payload)

        # Rechercher les lights
        response = client.get("/api/devices/search/advanced?device_type=light")
        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 3
        assert data["count"] == 3

    def test_search_devices_by_room(self):
        """Teste la recherche filtrée par pièce"""
        # Créer des devices dans différentes pièces
        payload1 = {
            "device_id": "light_1",
            "name": "Light",
            "room_name": "Living Room",
            "device_type": "light",
        }
        payload2 = {
            "device_id": "light_2",
            "name": "Light",
            "room_name": "Bedroom",
            "device_type": "light",
        }
        client.post("/api/devices/build", json=payload1)
        client.post("/api/devices/build", json=payload2)

        # Rechercher dans Living Room
        response = client.get("/api/devices/search/advanced?room_name=Living%20Room")
        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 1
        assert data["count"] == 1

    def test_search_devices_by_manufacturer(self):
        """Teste la recherche filtrée par fabricant"""
        # Créer des devices de différents fabricants
        for i, manufacturer in enumerate(["philips", "nest"]):
            payload = {
                "device_id": f"light_{i}",
                "name": f"Light {i}",
                "room_name": "Room",
                "device_type": "light",
                "manufacturer": manufacturer,
            }
            client.post("/api/devices/build", json=payload)

        # Rechercher Philips
        response = client.get("/api/devices/search/advanced?manufacturer=Philips")
        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 1

    def test_search_devices_with_multiple_filters(self):
        """Teste la recherche avec plusieurs filtres"""
        # Créer des devices
        payload1 = {
            "device_id": "light_1",
            "name": "Light",
            "room_name": "Living Room",
            "device_type": "light",
            "manufacturer": "philips",
        }
        payload2 = {
            "device_id": "light_2",
            "name": "Light",
            "room_name": "Living Room",
            "device_type": "light",
            "manufacturer": "nest",
        }
        payload3 = {
            "device_id": "thermo_1",
            "name": "Thermostat",
            "room_name": "Living Room",
            "device_type": "thermostat",
            "manufacturer": "philips",
        }
        client.post("/api/devices/build", json=payload1)
        client.post("/api/devices/build", json=payload2)
        client.post("/api/devices/build", json=payload3)

        # Rechercher light + Philips dans Living Room
        response = client.get(
            "/api/devices/search/advanced?device_type=light&room_name=Living%20Room&manufacturer=Philips"
        )
        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 1

    def test_get_devices_stats_summary(self):
        """Teste les statistiques résumées"""
        # Créer des devices
        for i in range(2):
            payload = {
                "device_id": f"light_{i}",
                "name": f"Light {i}",
                "room_name": "Living Room",
                "device_type": "light",
                "manufacturer": "philips",
            }
            client.post("/api/devices/build", json=payload)

        payload = {
            "device_id": "thermo_1",
            "name": "Thermostat",
            "room_name": "Bedroom",
            "device_type": "thermostat",
            "manufacturer": "nest",
        }
        client.post("/api/devices/build", json=payload)

        response = client.get("/api/devices/stats/summary")
        assert response.status_code == 200
        data = response.json()
        assert data["total_devices"] == 3
        assert data["by_type"]["light"] == 2
        assert data["by_type"]["thermostat"] == 1
        assert data["by_room"]["Living Room"] == 2
        assert data["by_room"]["Bedroom"] == 1

    def test_get_devices_stats_by_type(self):
        """Teste les statistiques détaillées par type"""
        # Créer des lights
        for i in range(2):
            payload = {
                "device_id": f"light_{i}",
                "name": f"Light {i}",
                "room_name": "Room",
                "device_type": "light",
            }
            client.post("/api/devices/build", json=payload)

        response = client.get("/api/devices/stats/types")
        assert response.status_code == 200
        data = response.json()
        assert "by_type" in data
        assert data["by_type"]["light"]["count"] == 2

    def test_get_devices_stats_by_room(self):
        """Teste les statistiques détaillées par pièce"""
        # Créer des devices
        for i in range(2):
            payload = {
                "device_id": f"light_{i}",
                "name": f"Light {i}",
                "room_name": "Living Room",
                "device_type": "light",
            }
            client.post("/api/devices/build", json=payload)

        response = client.get("/api/devices/stats/rooms")
        assert response.status_code == 200
        data = response.json()
        assert "by_room" in data
        assert data["by_room"]["Living Room"]["count"] == 2

    def test_get_devices_stats_by_manufacturer(self):
        """Teste les statistiques détaillées par fabricant"""
        # Créer des devices Philips
        for i in range(2):
            payload = {
                "device_id": f"light_{i}",
                "name": f"Light {i}",
                "room_name": "Room",
                "device_type": "light",
                "manufacturer": "philips",
            }
            client.post("/api/devices/build", json=payload)

        response = client.get("/api/devices/stats/manufacturers")
        assert response.status_code == 200
        data = response.json()
        assert "by_manufacturer" in data
        assert data["by_manufacturer"]["Philips"]["count"] == 2