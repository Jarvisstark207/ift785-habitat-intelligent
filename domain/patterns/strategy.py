"""Pattern Strategy - Strategies de controle de la maison"""

from abc import ABC, abstractmethod


class HomeControlStrategy(ABC):
    """Interface Strategy pour le controle de la maison intelligente"""

    @abstractmethod
    def get_target_temperature(self) -> float:
        """Retourne la temperature cible du profil"""
        pass

    @abstractmethod
    def get_light_behavior(self) -> dict:
        """Retourne le comportement des lumieres"""
        pass

    @abstractmethod
    def get_alert_thresholds(self) -> dict:
        """Retourne les seuils d'alertes"""
        pass

    @abstractmethod
    def get_strategy_name(self) -> str:
        """Retourne le nom de la strategie"""
        pass

    def apply(self) -> dict:
        """Applique la strategie et retourne la configuration complete"""
        return {
            "strategy": self.get_strategy_name(),
            "target_temperature": self.get_target_temperature(),
            "light_behavior": self.get_light_behavior(),
            "alert_thresholds": self.get_alert_thresholds(),
        }


class EconomyStrategy(HomeControlStrategy):
    """Strategie economie d'energie: temperature basse, lumieres auto-off"""

    def get_target_temperature(self) -> float:
        return 19.0

    def get_light_behavior(self) -> dict:
        return {
            "auto_off_minutes": 5,
            "max_brightness": 70,
            "prefer_natural": True,
        }

    def get_alert_thresholds(self) -> dict:
        return {
            "temp_min": 16.0,
            "temp_max": 24.0,
            "consumption_max": 1500.0,
        }

    def get_strategy_name(self) -> str:
        return "economy"


class ComfortStrategy(HomeControlStrategy):
    """Strategie confort: temperature agreable, lumieres adaptatives"""

    def get_target_temperature(self) -> float:
        return 21.0

    def get_light_behavior(self) -> dict:
        return {
            "auto_off_minutes": 30,
            "max_brightness": 100,
            "prefer_natural": False,
            "time_based": True,
        }

    def get_alert_thresholds(self) -> dict:
        return {
            "temp_min": 18.0,
            "temp_max": 25.0,
            "consumption_max": 2000.0,
        }

    def get_strategy_name(self) -> str:
        return "comfort"


class AbsenceStrategy(HomeControlStrategy):
    """Strategie absence: temperature minimale, simulation de presence"""

    def get_target_temperature(self) -> float:
        return 16.0

    def get_light_behavior(self) -> dict:
        return {
            "auto_off_minutes": 0,
            "max_brightness": 0,
            "presence_simulation": True,
            "simulation_hours": {"start": 18, "end": 22},
        }

    def get_alert_thresholds(self) -> dict:
        return {
            "temp_min": 10.0,
            "temp_max": 30.0,
            "consumption_max": 500.0,
            "security_max": True,
        }

    def get_strategy_name(self) -> str:
        return "absence"


STRATEGY_MAP = {
    "economy": EconomyStrategy,
    "comfort": ComfortStrategy,
    "absence": AbsenceStrategy,
}


def get_strategy(strategy_type: str) -> HomeControlStrategy:
    """Fabrique de strategies"""
    strategy_class = STRATEGY_MAP.get(strategy_type)
    if strategy_class is None:
        raise ValueError(f"Strategie inconnue: {strategy_type}")
    return strategy_class()
