"""Tests pour les patterns GoF (Factory, Abstract Factory, Builder, Singleton)"""

import pytest

from domain.models.device import CO2Sensor, Light, MotionSensor, Thermostat
from domain.models.device_builder import DeviceBuilder
from domain.models.device_factory import (
    DeviceFactoryProvider,
    GenericFactory,
    NestFactory,
    PhilipsFactory,
)
from domain.models.device_registry import DeviceRegistry
from application.services.device_service import DeviceService


class TestDeviceModels:
    """Tests pour les modèles de devices"""

    def test_light_creation(self):
        """Teste la création d'une ampoule"""
        light = Light(
            device_id="light_1",
            name="Living Room Light",
            room_name="Living Room",
            device_type="light",
            manufacturer="Philips",
            brightness=80,
            color="warm",
        )
        assert light.device_id == "light_1"
        assert light.name == "Living Room Light"
        assert light.brightness == 80
        assert light.color == "warm"

    def test_light_status(self):
        """Teste le statut d'une ampoule"""
        light = Light(
            device_id="light_1",
            name="Test Light",
            room_name="Room",
            device_type="light",
        )
        status = light.get_status()
        assert status["device_id"] == "light_1"
        assert status["brightness"] == 100
        assert status["color"] == "white"

    def test_light_to_dict(self):
        """Teste la conversion d'une ampoule en dictionnaire"""
        light = Light(
            device_id="light_1",
            name="Test Light",
            room_name="Room",
            device_type="light",
        )
        device_dict = light.to_dict()
        assert "device_id" in device_dict
        assert "name" in device_dict
        assert "brightness" in device_dict

    def test_thermostat_creation(self):
        """Teste la création d'un thermostat"""
        thermostat = Thermostat(
            device_id="thermo_1",
            name="Living Room Thermostat",
            room_name="Living Room",
            device_type="thermostat",
            manufacturer="Nest",
            temperature=22.0,
            target_temperature=21.0,
            mode="cool",
        )
        assert thermostat.device_id == "thermo_1"
        assert thermostat.temperature == 22.0
        assert thermostat.mode == "cool"

    def test_thermostat_status(self):
        """Teste le statut d'un thermostat"""
        thermostat = Thermostat(
            device_id="thermo_1",
            name="Test Thermostat",
            room_name="Room",
            device_type="thermostat",
        )
        status = thermostat.get_status()
        assert status["temperature"] == 20.0
        assert status["target_temperature"] == 20.0
        assert status["mode"] == "auto"

    def test_co2_sensor_creation(self):
        """Teste la création d'un capteur CO2"""
        co2_sensor = CO2Sensor(
            device_id="co2_1",
            name="Office CO2 Sensor",
            room_name="Office",
            device_type="co2_sensor",
            ppm=800.0,
            alarm_threshold=1200.0,
        )
        assert co2_sensor.device_id == "co2_1"
        assert co2_sensor.ppm == 800.0
        assert co2_sensor.alarm_threshold == 1200.0

    def test_co2_sensor_alarm(self):
        """Teste l'alarme du capteur CO2"""
        co2_sensor = CO2Sensor(
            device_id="co2_1",
            name="Test CO2",
            room_name="Room",
            device_type="co2_sensor",
            ppm=1500.0,
            alarm_threshold=1000.0,
        )
        status = co2_sensor.get_status()
        assert status["alarm_active"] is True

    def test_motion_sensor_creation(self):
        """Teste la création d'un capteur de mouvement"""
        motion_sensor = MotionSensor(
            device_id="motion_1",
            name="Hallway Motion Sensor",
            room_name="Hallway",
            device_type="motion_sensor",
            motion_detected=True,
            sensitivity=7,
        )
        assert motion_sensor.device_id == "motion_1"
        assert motion_sensor.motion_detected is True
        assert motion_sensor.sensitivity == 7

    def test_motion_sensor_status(self):
        """Teste le statut d'un capteur de mouvement"""
        motion_sensor = MotionSensor(
            device_id="motion_1",
            name="Test Motion",
            room_name="Room",
            device_type="motion_sensor",
        )
        status = motion_sensor.get_status()
        assert "motion_detected" in status
        assert status["sensitivity"] == 5


class TestDeviceFactory:
    """Tests pour le Factory Method et Abstract Factory"""

    def test_philips_factory_light(self):
        """Teste la création d'une ampoule Philips"""
        factory = PhilipsFactory()
        light = factory.create_light(
            device_id="light_1",
            name="Hue Bulb",
            room_name="Room",
            brightness=75,
        )
        assert isinstance(light, Light)
        assert light.manufacturer == "Philips"
        assert light.brightness == 75

    def test_philips_factory_thermostat(self):
        """Teste la création d'un thermostat Philips"""
        factory = PhilipsFactory()
        thermostat = factory.create_thermostat(
            device_id="thermo_1",
            name="Philips Thermostat",
            room_name="Room",
        )
        assert isinstance(thermostat, Thermostat)
        assert thermostat.manufacturer == "Philips"

    def test_philips_factory_co2_sensor(self):
        """Teste la création d'un capteur CO2 Philips"""
        factory = PhilipsFactory()
        co2_sensor = factory.create_co2_sensor(
            device_id="co2_1",
            name="Philips CO2",
            room_name="Room",
        )
        assert isinstance(co2_sensor, CO2Sensor)
        assert co2_sensor.manufacturer == "Philips"

    def test_philips_factory_motion_sensor(self):
        """Teste la création d'un capteur de mouvement Philips"""
        factory = PhilipsFactory()
        motion_sensor = factory.create_motion_sensor(
            device_id="motion_1",
            name="Philips Motion",
            room_name="Room",
        )
        assert isinstance(motion_sensor, MotionSensor)
        assert motion_sensor.manufacturer == "Philips"

    def test_nest_factory_thermostat(self):
        """Teste la création d'un thermostat Nest"""
        factory = NestFactory()
        thermostat = factory.create_thermostat(
            device_id="thermo_1",
            name="Nest Thermostat",
            room_name="Room",
            temperature=21.5,
            mode="heat",
        )
        assert isinstance(thermostat, Thermostat)
        assert thermostat.manufacturer == "Google Nest"
        assert thermostat.temperature == 21.5
        assert thermostat.mode == "heat"

    def test_generic_factory_light(self):
        """Teste la création d'une ampoule générique"""
        factory = GenericFactory()
        light = factory.create_light(
            device_id="light_1",
            name="Generic Light",
            room_name="Room",
        )
        assert isinstance(light, Light)
        assert light.manufacturer == "Generic"

    def test_factory_provider_philips(self):
        """Teste le provider de fabrique pour Philips"""
        factory = DeviceFactoryProvider.get_factory("philips")
        assert isinstance(factory, PhilipsFactory)

    def test_factory_provider_nest(self):
        """Teste le provider de fabrique pour Nest"""
        factory = DeviceFactoryProvider.get_factory("nest")
        assert isinstance(factory, NestFactory)

    def test_factory_provider_generic(self):
        """Teste le provider de fabrique pour générique"""
        factory = DeviceFactoryProvider.get_factory("generic")
        assert isinstance(factory, GenericFactory)

    def test_factory_provider_case_insensitive(self):
        """Teste que le provider est insensible à la casse"""
        factory = DeviceFactoryProvider.get_factory("PHILIPS")
        assert isinstance(factory, PhilipsFactory)

    def test_factory_provider_unknown_returns_generic(self):
        """Teste que le provider retourne generic pour un fabricant inconnu"""
        factory = DeviceFactoryProvider.get_factory("unknown")
        assert isinstance(factory, GenericFactory)


class TestDeviceBuilder:
    """Tests pour le Builder pattern"""

    def test_builder_light(self):
        """Teste la création d'une ampoule avec le builder"""
        builder = DeviceBuilder()
        light = (
            builder.set_device_id("light_1")
            .set_name("Test Light")
            .set_room_name("Room")
            .set_device_type("light")
            .set_brightness(50)
            .set_color("red")
            .build()
        )
        assert isinstance(light, Light)
        assert light.brightness == 50
        assert light.color == "red"

    def test_builder_thermostat(self):
        """Teste la création d'un thermostat avec le builder"""
        builder = DeviceBuilder()
        thermostat = (
            builder.set_device_id("thermo_1")
            .set_name("Test Thermostat")
            .set_room_name("Room")
            .set_device_type("thermostat")
            .set_temperature(22.0)
            .set_target_temperature(21.0)
            .set_mode("heat")
            .build()
        )
        assert isinstance(thermostat, Thermostat)
        assert thermostat.temperature == 22.0
        assert thermostat.mode == "heat"

    def test_builder_co2_sensor(self):
        """Teste la création d'un capteur CO2 avec le builder"""
        builder = DeviceBuilder()
        co2_sensor = (
            builder.set_device_id("co2_1")
            .set_name("Test CO2")
            .set_room_name("Room")
            .set_device_type("co2_sensor")
            .set_ppm(900.0)
            .set_alarm_threshold(1200.0)
            .build()
        )
        assert isinstance(co2_sensor, CO2Sensor)
        assert co2_sensor.ppm == 900.0
        assert co2_sensor.alarm_threshold == 1200.0

    def test_builder_motion_sensor(self):
        """Teste la création d'un capteur de mouvement avec le builder"""
        builder = DeviceBuilder()
        motion_sensor = (
            builder.set_device_id("motion_1")
            .set_name("Test Motion")
            .set_room_name("Room")
            .set_device_type("motion_sensor")
            .set_motion_detected(True)
            .set_sensitivity(8)
            .build()
        )
        assert isinstance(motion_sensor, MotionSensor)
        assert motion_sensor.motion_detected is True
        assert motion_sensor.sensitivity == 8

    def test_builder_with_manufacturer(self):
        """Teste le builder avec un fabricant spécifique"""
        builder = DeviceBuilder()
        light = (
            builder.set_device_id("light_1")
            .set_name("Hue Light")
            .set_room_name("Room")
            .set_device_type("light")
            .set_manufacturer("philips")
            .build()
        )
        assert light.manufacturer == "Philips"

    def test_builder_missing_device_id(self):
        """Teste que le builder lève une erreur sans device_id"""
        builder = DeviceBuilder()
        with pytest.raises(ValueError):
            (
                builder.set_name("Test")
                .set_room_name("Room")
                .set_device_type("light")
                .build()
            )

    def test_builder_missing_name(self):
        """Teste que le builder lève une erreur sans name"""
        builder = DeviceBuilder()
        with pytest.raises(ValueError):
            (
                builder.set_device_id("light_1")
                .set_room_name("Room")
                .set_device_type("light")
                .build()
            )

    def test_builder_missing_room_name(self):
        """Teste que le builder lève une erreur sans room_name"""
        builder = DeviceBuilder()
        with pytest.raises(ValueError):
            (
                builder.set_device_id("light_1")
                .set_name("Test")
                .set_device_type("light")
                .build()
            )

    def test_builder_missing_device_type(self):
        """Teste que le builder lève une erreur sans device_type"""
        builder = DeviceBuilder()
        with pytest.raises(ValueError):
            (
                builder.set_device_id("light_1")
                .set_name("Test")
                .set_room_name("Room")
                .build()
            )

    def test_builder_invalid_device_type(self):
        """Teste que le builder lève une erreur avec un type invalide"""
        builder = DeviceBuilder()
        with pytest.raises(ValueError):
            (
                builder.set_device_id("dev_1")
                .set_name("Test")
                .set_room_name("Room")
                .set_device_type("invalid_type")
                .build()
            )

    def test_builder_reset(self):
        """Teste la réinitialisation du builder"""
        builder = DeviceBuilder()
        builder.set_device_id("light_1").set_name("Light").reset()
        with pytest.raises(ValueError):
            builder.build()

    def test_builder_invalid_brightness(self):
        """Teste que le builder ignore les valeurs invalides de luminosité"""
        builder = DeviceBuilder()
        light = (
            builder.set_device_id("light_1")
            .set_name("Light")
            .set_room_name("Room")
            .set_device_type("light")
            .set_brightness(150)
            .build()
        )
        # La luminosité reste à 100 car 150 > 100
        assert light.brightness == 100

    def test_builder_invalid_sensitivity(self):
        """Teste que le builder ignore les valeurs invalides de sensibilité"""
        builder = DeviceBuilder()
        motion_sensor = (
            builder.set_device_id("motion_1")
            .set_name("Motion")
            .set_room_name("Room")
            .set_device_type("motion_sensor")
            .set_sensitivity(15)
            .build()
        )
        # La sensibilité reste à 5 car 15 > 10
        assert motion_sensor.sensitivity == 5


class TestDeviceRegistry:
    """Tests pour le Singleton pattern"""

    def setup_method(self):
        """Nettoie le registre avant chaque test"""
        registry = DeviceRegistry.get_instance()
        registry.clear()

    def test_singleton_instance(self):
        """Teste que le registre est un singleton"""
        registry1 = DeviceRegistry.get_instance()
        registry2 = DeviceRegistry.get_instance()
        assert registry1 is registry2

    def test_register_device(self):
        """Teste l'enregistrement d'un device"""
        registry = DeviceRegistry.get_instance()
        light = Light(
            device_id="light_1",
            name="Test",
            room_name="Room",
            device_type="light",
        )
        registry.register(light)
        assert registry.get("light_1") == light

    def test_unregister_device(self):
        """Teste la désinscription d'un device"""
        registry = DeviceRegistry.get_instance()
        light = Light(
            device_id="light_1",
            name="Test",
            room_name="Room",
            device_type="light",
        )
        registry.register(light)
        assert registry.unregister("light_1") is True
        assert registry.get("light_1") is None

    def test_get_all_devices(self):
        """Teste la récupération de tous les devices"""
        registry = DeviceRegistry.get_instance()
        light = Light(
            device_id="light_1",
            name="Light",
            room_name="Room",
            device_type="light",
        )
        thermostat = Thermostat(
            device_id="thermo_1",
            name="Thermostat",
            room_name="Room",
            device_type="thermostat",
        )
        registry.register(light)
        registry.register(thermostat)
        devices = registry.get_all()
        assert len(devices) == 2

    def test_get_by_type(self):
        """Teste la récupération des devices par type"""
        registry = DeviceRegistry.get_instance()
        light = Light(
            device_id="light_1",
            name="Light",
            room_name="Room",
            device_type="light",
        )
        thermostat = Thermostat(
            device_id="thermo_1",
            name="Thermostat",
            room_name="Room",
            device_type="thermostat",
        )
        registry.register(light)
        registry.register(thermostat)
        lights = registry.get_by_type("light")
        assert len(lights) == 1
        assert lights[0].device_id == "light_1"

    def test_get_by_room(self):
        """Teste la récupération des devices par pièce"""
        registry = DeviceRegistry.get_instance()
        light1 = Light(
            device_id="light_1",
            name="Light",
            room_name="Room1",
            device_type="light",
        )
        light2 = Light(
            device_id="light_2",
            name="Light",
            room_name="Room2",
            device_type="light",
        )
        registry.register(light1)
        registry.register(light2)
        devices = registry.get_by_room("Room1")
        assert len(devices) == 1
        assert devices[0].room_name == "Room1"

    def test_get_by_manufacturer(self):
        """Teste la récupération des devices par fabricant"""
        registry = DeviceRegistry.get_instance()
        factory = PhilipsFactory()
        light = factory.create_light(
            device_id="light_1",
            name="Light",
            room_name="Room",
        )
        registry.register(light)
        devices = registry.get_by_manufacturer("Philips")
        assert len(devices) == 1
        assert devices[0].manufacturer == "Philips"

    def test_exists(self):
        """Teste la vérification d'existence d'un device"""
        registry = DeviceRegistry.get_instance()
        light = Light(
            device_id="light_1",
            name="Light",
            room_name="Room",
            device_type="light",
        )
        registry.register(light)
        assert registry.exists("light_1") is True
        assert registry.exists("light_2") is False

    def test_count(self):
        """Teste le comptage des devices"""
        registry = DeviceRegistry.get_instance()
        light = Light(
            device_id="light_1",
            name="Light",
            room_name="Room",
            device_type="light",
        )
        thermostat = Thermostat(
            device_id="thermo_1",
            name="Thermostat",
            room_name="Room",
            device_type="thermostat",
        )
        registry.register(light)
        registry.register(thermostat)
        assert registry.count() == 2


class TestDeviceService:
    """Tests pour le service de devices"""

    def setup_method(self):
        """Initialise le service pour chaque test"""
        registry = DeviceRegistry.get_instance()
        registry.clear()
        self.service = DeviceService()

    def test_build_light_device(self):
        """Teste la construction d'une ampoule via le service"""
        config = {
            "device_id": "light_1",
            "name": "Living Room Light",
            "room_name": "Living Room",
            "device_type": "light",
            "brightness": 75,
            "color": "warm",
        }
        device = self.service.build_device(config)
        assert isinstance(device, Light)
        assert device.brightness == 75
        assert device.color == "warm"

    def test_build_thermostat_device(self):
        """Teste la construction d'un thermostat via le service"""
        config = {
            "device_id": "thermo_1",
            "name": "Living Room Thermostat",
            "room_name": "Living Room",
            "device_type": "thermostat",
            "temperature": 22.0,
            "target_temperature": 21.0,
            "mode": "cool",
        }
        device = self.service.build_device(config)
        assert isinstance(device, Thermostat)
        assert device.temperature == 22.0
        assert device.mode == "cool"

    def test_build_co2_device(self):
        """Teste la construction d'un capteur CO2 via le service"""
        config = {
            "device_id": "co2_1",
            "name": "Office CO2 Sensor",
            "room_name": "Office",
            "device_type": "co2_sensor",
            "ppm": 800.0,
            "alarm_threshold": 1200.0,
        }
        device = self.service.build_device(config)
        assert isinstance(device, CO2Sensor)
        assert device.ppm == 800.0

    def test_build_motion_device(self):
        """Teste la construction d'un capteur de mouvement via le service"""
        config = {
            "device_id": "motion_1",
            "name": "Hallway Motion Sensor",
            "room_name": "Hallway",
            "device_type": "motion_sensor",
            "sensitivity": 7,
        }
        device = self.service.build_device(config)
        assert isinstance(device, MotionSensor)
        assert device.sensitivity == 7

    def test_build_device_missing_required_fields(self):
        """Teste la construction d'un device sans champs obligatoires"""
        config = {
            "device_id": "light_1",
            "name": "Light",
        }
        with pytest.raises(ValueError):
            self.service.build_device(config)

    def test_get_device(self):
        """Teste la récupération d'un device"""
        config = {
            "device_id": "light_1",
            "name": "Light",
            "room_name": "Room",
            "device_type": "light",
        }
        self.service.build_device(config)
        device = self.service.get_device("light_1")
        assert device.device_id == "light_1"

    def test_get_nonexistent_device(self):
        """Teste la récupération d'un device qui n'existe pas"""
        with pytest.raises(ValueError):
            self.service.get_device("nonexistent")

    def test_get_all_devices(self):
        """Teste la récupération de tous les devices"""
        config1 = {
            "device_id": "light_1",
            "name": "Light",
            "room_name": "Room",
            "device_type": "light",
        }
        config2 = {
            "device_id": "thermo_1",
            "name": "Thermostat",
            "room_name": "Room",
            "device_type": "thermostat",
        }
        self.service.build_device(config1)
        self.service.build_device(config2)
        devices = self.service.get_all_devices()
        assert len(devices) == 2

    def test_delete_device(self):
        """Teste la suppression d'un device"""
        config = {
            "device_id": "light_1",
            "name": "Light",
            "room_name": "Room",
            "device_type": "light",
        }
        self.service.build_device(config)
        assert self.service.delete_device("light_1") is True
        assert self.service.device_exists("light_1") is False

    def test_device_exists(self):
        """Teste la vérification d'existence d'un device"""
        config = {
            "device_id": "light_1",
            "name": "Light",
            "room_name": "Room",
            "device_type": "light",
        }
        self.service.build_device(config)
        assert self.service.device_exists("light_1") is True
        assert self.service.device_exists("light_2") is False

    def test_get_device_count(self):
        """Teste le comptage des devices"""
        for i in range(5):
            config = {
                "device_id": f"light_{i}",
                "name": f"Light {i}",
                "room_name": "Room",
                "device_type": "light",
            }
            self.service.build_device(config)
        assert self.service.get_device_count() == 5
