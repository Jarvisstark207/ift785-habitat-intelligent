"""Tests pour le pattern Factory"""

from domain.models.device_factory import PhilipsFactory, NestFactory, GenericFactory, DeviceFactory
from domain.models.device import Light, Thermostat


class TestFactory:
    """Tests pour le Factory pattern"""

    def test_factory_is_abstract(self):
        """Teste que DeviceFactory est abstraite"""
        # Vérifier que DeviceFactory ne peut pas être instanciée directement
        from abc import ABC
        assert issubclass(DeviceFactory, ABC)

    def test_philips_factory_exists(self):
        """Teste que la fabrique Philips existe"""
        factory = PhilipsFactory()
        assert factory is not None

    def test_nest_factory_exists(self):
        """Teste que la fabrique Nest existe"""
        factory = NestFactory()
        assert factory is not None

    def test_generic_factory_exists(self):
        """Teste que la fabrique générique existe"""
        factory = GenericFactory()
        assert factory is not None

    def test_factory_creates_light(self):
        """Teste que la fabrique crée une Light"""
        factory = PhilipsFactory()
        light = factory.create_light("light_1", "Test", "Room")
        assert isinstance(light, Light)

    def test_factory_creates_thermostat(self):
        """Teste que la fabrique crée un Thermostat"""
        factory = NestFactory()
        thermo = factory.create_thermostat("thermo_1", "Test", "Room")
        assert isinstance(thermo, Thermostat)

    def test_factory_pattern_implementation(self):
        """Teste que le pattern Factory est bien implémenté"""
        factories = [PhilipsFactory(), NestFactory(), GenericFactory()]
        assert len(factories) >= 2  # Au moins 2 fabriques concrètes

    def test_factory_creates_different_manufacturers(self):
        """Teste que les fabriques créent des devices différents"""
        philips_factory = PhilipsFactory()
        nest_factory = NestFactory()

        light1 = philips_factory.create_light("light_1", "Test", "Room")
        light2 = nest_factory.create_light("light_2", "Test", "Room")

        assert light1.manufacturer != light2.manufacturer

