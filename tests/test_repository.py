"""Tests pour le pattern Repository"""

from domain.models.device_registry import DeviceRegistry
from domain.models.device import Light, Thermostat


class TestRepository:
    """Tests pour le Repository pattern (implémenté via DeviceRegistry)"""

    def setup_method(self):
        """Nettoie le registre avant chaque test"""
        registry = DeviceRegistry.get_instance()
        registry.clear()

    def test_repository_is_singleton(self):
        """Teste que le Repository est un Singleton"""
        registry1 = DeviceRegistry.get_instance()
        registry2 = DeviceRegistry.get_instance()
        assert registry1 is registry2

    def test_repository_add(self):
        """Teste l'ajout d'un élément au repository"""
        registry = DeviceRegistry.get_instance()
        light = Light(
            device_id="light_1",
            name="Test",
            room_name="Room",
            device_type="light",
        )
        registry.register(light)
        assert registry.get("light_1") is not None

    def test_repository_get(self):
        """Teste la récupération d'un élément"""
        registry = DeviceRegistry.get_instance()
        light = Light(
            device_id="light_1",
            name="Test",
            room_name="Room",
            device_type="light",
        )
        registry.register(light)
        retrieved = registry.get("light_1")
        assert retrieved.device_id == "light_1"

    def test_repository_delete(self):
        """Teste la suppression d'un élément"""
        registry = DeviceRegistry.get_instance()
        light = Light(
            device_id="light_1",
            name="Test",
            room_name="Room",
            device_type="light",
        )
        registry.register(light)
        registry.unregister("light_1")
        assert registry.get("light_1") is None

    def test_repository_get_all(self):
        """Teste la récupération de tous les éléments"""
        registry = DeviceRegistry.get_instance()
        for i in range(3):
            light = Light(
                device_id=f"light_{i}",
                name=f"Light {i}",
                room_name="Room",
                device_type="light",
            )
            registry.register(light)
        devices = registry.get_all()
        assert len(devices) == 3

    def test_repository_query_by_type(self):
        """Teste la requête par type (repository pattern)"""
        registry = DeviceRegistry.get_instance()
        light = Light(
            device_id="light_1",
            name="Light",
            room_name="Room",
            device_type="light",
        )
        thermo = Thermostat(
            device_id="thermo_1",
            name="Thermostat",
            room_name="Room",
            device_type="thermostat",
        )
        registry.register(light)
        registry.register(thermo)

        lights = registry.get_by_type("light")
        assert len(lights) == 1
        assert lights[0].device_id == "light_1"

    def test_repository_pattern_implementation(self):
        """Teste que le pattern Repository est implémenté"""
        registry = DeviceRegistry.get_instance()
        # Vérifier que les méthodes CRUD sont présentes
        assert hasattr(registry, "register")
        assert hasattr(registry, "get")
        assert hasattr(registry, "unregister")
        assert hasattr(registry, "get_all")

    def test_repository_exists_method(self):
        """Teste la méthode exists du repository"""
        registry = DeviceRegistry.get_instance()
        light = Light(
            device_id="light_1",
            name="Test",
            room_name="Room",
            device_type="light",
        )
        registry.register(light)
        assert registry.exists("light_1") is True
        assert registry.exists("light_2") is False
