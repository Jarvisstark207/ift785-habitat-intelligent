"""
Registre de devices par métaclasse - Itération 8 : Méta-programmation

DeviceMeta  : métaclasse qui enregistre automatiquement chaque sous-classe dans device_registry
DeviceBase  : classe de base utilisant DeviceMeta + descripteurs de validation
Classes concrètes : TemperatureSensor, MotionDetector, HumiditySensor
"""

from abc import ABCMeta

from app.core.descriptors import TypedField, RangedField


class DeviceMeta(ABCMeta):
    """
    Métaclasse qui enregistre automatiquement chaque sous-classe Device dans un registre central.
    Hérite de ABCMeta pour maintenir la compatibilité avec les classes abstraites.
    """
    registry = {}
    device_registry = {}

    def __new__(mcs, name, bases, namespace):
        cls = super().__new__(mcs, name, bases, namespace)
        if bases:
            DeviceMeta.registry[name] = cls
            DeviceMeta.device_registry[name] = cls
        return cls

    @classmethod
    def get_registry(mcs):
        """Retourne le registre des types enregistrés."""
        return dict(mcs.registry)

    @classmethod
    def get_device_class(mcs, type_name: str):
        """Retourne la classe correspondant au nom de type, ou None."""
        return mcs.registry.get(type_name)


class DeviceBase(metaclass=DeviceMeta):
    """
    Classe de base pour les devices avec validation par descripteurs.
    Toute sous-classe est enregistrée automatiquement dans DeviceMeta.registry.
    """
    name = TypedField(str, max_length=128)
    status = TypedField(str, allowed=["active", "inactive", "error"])

    def __init__(self, name: str = "Unknown", status: str = "active"):
        self.name = name
        self.status = status

    def to_dict(self) -> dict:
        return {
            "type": type(self).__name__,
            "name": self.name,
            "status": self.status,
        }

    def __repr__(self) -> str:
        return f"{type(self).__name__}(name={self.name!r}, status={self.status!r})"


class TemperatureSensor(DeviceBase):
    """Capteur de température — s'enregistre automatiquement dans DeviceMeta.registry."""
    temperature = RangedField(min_val=-50, max_val=100)

    def __init__(
        self,
        name: str = "TemperatureSensor",
        temperature: float = 20.0,
        status: str = "active",
    ):
        super().__init__(name=name, status=status)
        self.temperature = temperature

    def to_dict(self) -> dict:
        d = super().to_dict()
        d["temperature"] = self.temperature
        return d


class MotionDetector(DeviceBase):
    """Détecteur de mouvement — s'enregistre automatiquement dans DeviceMeta.registry."""
    sensitivity = RangedField(min_val=1, max_val=10)

    def __init__(
        self,
        name: str = "MotionDetector",
        sensitivity: int = 5,
        status: str = "active",
    ):
        super().__init__(name=name, status=status)
        self.sensitivity = sensitivity

    def to_dict(self) -> dict:
        d = super().to_dict()
        d["sensitivity"] = self.sensitivity
        return d


class HumiditySensor(DeviceBase):
    """Capteur d'humidité — s'enregistre automatiquement dans DeviceMeta.registry."""
    humidity = RangedField(min_val=0, max_val=100)

    def __init__(
        self,
        name: str = "HumiditySensor",
        humidity: float = 50.0,
        status: str = "active",
    ):
        super().__init__(name=name, status=status)
        self.humidity = humidity

    def to_dict(self) -> dict:
        d = super().to_dict()
        d["humidity"] = self.humidity
        return d



