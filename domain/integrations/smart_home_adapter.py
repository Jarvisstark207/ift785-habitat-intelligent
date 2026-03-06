"""Pattern Adapter - Adaptation d'APIs tierces vers une interface commune"""

from abc import ABC, abstractmethod
from typing import List


class SmartHomeAdapter(ABC):
    """Interface commune pour toutes les integrations domotiques.

    Permet d'utiliser des APIs tierces (Philips Hue, Nest, etc.)
    de facon uniforme sans connaitre leurs details d'implementation.
    """

    @abstractmethod
    def get_status(self) -> dict:
        """Retourne le statut general du systeme"""
        pass

    @abstractmethod
    def get_devices(self) -> List[dict]:
        """Retourne la liste des appareils disponibles"""
        pass

    @abstractmethod
    def control_device(self, device_id: str, command: dict) -> dict:
        """Envoie une commande a un appareil"""
        pass

    @abstractmethod
    def get_adapter_name(self) -> str:
        """Retourne le nom de l'integration"""
        pass


class PhilipsHueAdapter(SmartHomeAdapter):
    """Adapte l'API Philips Hue Bridge vers l'interface SmartHomeAdapter.

    L'API Hue utilise des groupes/scenes et des etats RGB.
    On les convertit en commandes generiques on/off + luminosite.
    """

    def __init__(self, bridge_ip: str = "192.168.1.100"):
        self._bridge_ip = bridge_ip
        self._lights = {
            "hue_001": {"name": "Salon", "on": True, "brightness": 80, "color": "warm"},
            "hue_002": {"name": "Chambre", "on": False, "brightness": 50, "color": "cool"},
            "hue_003": {"name": "Cuisine", "on": True, "brightness": 100, "color": "daylight"},
        }

    def get_status(self) -> dict:
        """Traduit le statut du bridge Hue en format generique"""
        active = sum(1 for light in self._lights.values() if light["on"])
        return {
            "adapter": self.get_adapter_name(),
            "connected": True,
            "bridge_ip": self._bridge_ip,
            "total_devices": len(self._lights),
            "active_devices": active,
        }

    def get_devices(self) -> List[dict]:
        """Convertit les 'lights' Hue en appareils generiques"""
        devices = []
        for device_id, light in self._lights.items():
            devices.append({
                "id": device_id,
                "name": light["name"],
                "type": "light",
                "status": "on" if light["on"] else "off",
                "properties": {
                    "brightness": light["brightness"],
                    "color": light["color"],
                },
                "source": self.get_adapter_name(),
            })
        return devices

    def control_device(self, device_id: str, command: dict) -> dict:
        """Traduit une commande generique en appel API Hue"""
        if device_id not in self._lights:
            return {"success": False, "error": f"Device {device_id} not found"}
        action = command.get("action", "")
        if action == "turn_on":
            self._lights[device_id]["on"] = True
        elif action == "turn_off":
            self._lights[device_id]["on"] = False
        elif action == "set_brightness":
            self._lights[device_id]["brightness"] = command.get("value", 50)
        return {"success": True, "device_id": device_id, "action": action}

    def get_adapter_name(self) -> str:
        return "philips-hue"


class NestAdapter(SmartHomeAdapter):
    """Adapte l'API Google Nest vers l'interface SmartHomeAdapter.

    L'API Nest utilise des 'traits' et des 'structures'.
    On les convertit en appareils et commandes generiques.
    """

    def __init__(self, project_id: str = "nest-project-demo"):
        self._project_id = project_id
        self._devices = {
            "nest_therm_01": {
                "name": "Thermostat Principal",
                "type": "thermostat",
                "ambient_temp": 20.5,
                "target_temp": 21.0,
                "mode": "HEAT",
            },
            "nest_cam_01": {
                "name": "Camera Entree",
                "type": "camera",
                "streaming": True,
                "motion_detected": False,
            },
        }

    def get_status(self) -> dict:
        """Traduit le statut de la structure Nest en format generique"""
        return {
            "adapter": self.get_adapter_name(),
            "connected": True,
            "project_id": self._project_id,
            "total_devices": len(self._devices),
            "active_devices": len(self._devices),
        }

    def get_devices(self) -> List[dict]:
        """Convertit les 'devices' Nest en appareils generiques"""
        devices = []
        for device_id, device in self._devices.items():
            properties = {
                k: v for k, v in device.items()
                if k not in ("name", "type")
            }
            devices.append({
                "id": device_id,
                "name": device["name"],
                "type": device["type"],
                "status": "on",
                "properties": properties,
                "source": self.get_adapter_name(),
            })
        return devices

    def control_device(self, device_id: str, command: dict) -> dict:
        """Traduit une commande generique en trait Nest"""
        if device_id not in self._devices:
            return {"success": False, "error": f"Device {device_id} not found"}
        action = command.get("action", "")
        device = self._devices[device_id]
        if action == "set_temperature" and device["type"] == "thermostat":
            device["target_temp"] = command.get("value", 20.0)
        elif action == "set_mode" and device["type"] == "thermostat":
            device["mode"] = command.get("value", "HEAT")
        return {"success": True, "device_id": device_id, "action": action}

    def get_adapter_name(self) -> str:
        return "nest"
