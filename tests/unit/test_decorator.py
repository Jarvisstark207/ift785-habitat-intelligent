"""Tests unitaires - Pattern Decorator (LoggingDecorator, ValidationDecorator)"""

import pytest

from domain.integrations.smart_home_adapter import (
    PhilipsHueAdapter,
    NestAdapter,
)
from domain.integrations.decorators import (
    SmartHomeDecorator,
    LoggingDecorator,
    ValidationDecorator,
)


@pytest.fixture
def hue():
    return PhilipsHueAdapter()


@pytest.fixture
def logging_hue(hue):
    return LoggingDecorator(hue)


@pytest.fixture
def validation_hue(hue):
    return ValidationDecorator(hue)


class TestSmartHomeDecorator:

    def test_decorateur_base_delegue_status(self, hue):
        """Le decorateur base delegue get_status"""
        dec = SmartHomeDecorator(hue)
        assert dec.get_status() == hue.get_status()

    def test_decorateur_base_delegue_devices(self, hue):
        """Le decorateur base delegue get_devices"""
        dec = SmartHomeDecorator(hue)
        assert dec.get_devices() == hue.get_devices()

    def test_decorateur_base_delegue_nom(self, hue):
        dec = SmartHomeDecorator(hue)
        assert dec.get_adapter_name() == hue.get_adapter_name()

    def test_decorateur_base_delegue_control(self, hue):
        dec = SmartHomeDecorator(hue)
        result = dec.control_device("hue_001", {"action": "turn_on"})
        assert result["success"] is True


class TestLoggingDecorator:

    def test_log_vide_initialement(self, logging_hue):
        assert logging_hue.get_log_count() == 0

    def test_get_status_enregistre(self, logging_hue):
        logging_hue.get_status()
        assert logging_hue.get_log_count() == 1

    def test_get_devices_enregistre(self, logging_hue):
        logging_hue.get_devices()
        assert logging_hue.get_log_count() == 1

    def test_control_enregistre(self, logging_hue):
        logging_hue.control_device("hue_001", {"action": "turn_on"})
        assert logging_hue.get_log_count() == 1

    def test_plusieurs_appels_enregistres(self, logging_hue):
        logging_hue.get_status()
        logging_hue.get_devices()
        logging_hue.control_device("hue_001", {"action": "turn_off"})
        assert logging_hue.get_log_count() == 3

    def test_log_contient_methode(self, logging_hue):
        logging_hue.get_status()
        log = logging_hue.get_log()
        assert log[0]["method"] == "get_status"

    def test_log_contient_adapter_name(self, logging_hue):
        logging_hue.get_status()
        log = logging_hue.get_log()
        assert log[0]["adapter"] == "philips-hue"

    def test_log_contient_timestamp(self, logging_hue):
        logging_hue.get_status()
        log = logging_hue.get_log()
        assert "timestamp" in log[0]

    def test_clear_log(self, logging_hue):
        logging_hue.get_status()
        logging_hue.get_status()
        logging_hue.clear_log()
        assert logging_hue.get_log_count() == 0

    def test_get_status_retourne_valeur(self, logging_hue):
        """Le decorator ne modifie pas la valeur de retour"""
        status = logging_hue.get_status()
        assert status["adapter"] == "philips-hue"

    def test_get_devices_retourne_valeur(self, logging_hue):
        devices = logging_hue.get_devices()
        assert len(devices) == 3

    def test_logging_avec_nest(self):
        """Le decorator fonctionne avec n'importe quel adapter"""
        nest = LoggingDecorator(NestAdapter())
        nest.get_status()
        nest.get_devices()
        assert nest.get_log_count() == 2


class TestValidationDecorator:

    def test_get_status_valide(self, validation_hue):
        """get_status retourne un dict valide"""
        status = validation_hue.get_status()
        assert "adapter" in status

    def test_get_devices_valide(self, validation_hue):
        """get_devices retourne une liste valide"""
        devices = validation_hue.get_devices()
        assert len(devices) > 0

    def test_control_valide(self, validation_hue):
        result = validation_hue.control_device("hue_001", {"action": "turn_on"})
        assert result["success"] is True

    def test_control_device_id_vide_leve_erreur(self, validation_hue):
        with pytest.raises(ValueError):
            validation_hue.control_device("", {"action": "turn_on"})

    def test_control_command_invalide_leve_erreur(self, validation_hue):
        with pytest.raises(ValueError):
            validation_hue.control_device("hue_001", "turn_on")
