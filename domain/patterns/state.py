"""Pattern State - Etats de la maison intelligente"""

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from domain.house_states.house import House


class HouseState(ABC):
    """Etat abstrait de la maison - definit le comportement par mode"""

    @abstractmethod
    def on_enter(self, house: "House") -> None:
        """Actions lors de l'entree dans cet etat"""
        pass

    @abstractmethod
    def on_exit(self, house: "House") -> None:
        """Actions lors de la sortie de cet etat"""
        pass

    @abstractmethod
    def handle_presence_detected(self, house: "House") -> None:
        """Reaction a la detection de presence"""
        pass

    @abstractmethod
    def handle_night_time(self, house: "House") -> None:
        """Reaction au passage en mode nuit"""
        pass

    @abstractmethod
    def handle_day_time(self, house: "House") -> None:
        """Reaction au passage en mode jour"""
        pass

    @abstractmethod
    def get_mode_name(self) -> str:
        """Retourne le nom du mode"""
        pass

    @abstractmethod
    def get_mode_config(self) -> dict:
        """Retourne la configuration specifique du mode"""
        pass
