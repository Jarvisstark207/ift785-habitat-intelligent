"""Contexte de la machine a etats de la maison"""

from datetime import datetime
from typing import List

from domain.patterns.state import HouseState
from domain.house_states.states import DomicileState


class House:
    """Contexte du pattern State - represente la maison intelligente.

    Delegue son comportement a l'etat courant qui peut changer
    dynamiquement selon les evenements (presence, heure, etc.).
    """

    def __init__(self) -> None:
        self._state: HouseState = DomicileState()
        self._mode_history: List[dict] = []
        self._event_log: List[dict] = []
        self._state.on_enter(self)

    def set_state(self, state: HouseState) -> None:
        """Change l'etat courant de la maison"""
        old_mode = self._state.get_mode_name()
        self._state.on_exit(self)
        self._state = state
        new_mode = state.get_mode_name()
        self._mode_history.append({
            "from": old_mode,
            "to": new_mode,
            "timestamp": datetime.now().isoformat(),
        })
        self._state.on_enter(self)

    def log_event(self, message: str) -> None:
        """Enregistre un evenement dans le journal"""
        self._event_log.append({
            "message": message,
            "timestamp": datetime.now().isoformat(),
        })

    def get_current_mode(self) -> str:
        """Retourne le mode actuel"""
        return self._state.get_mode_name()

    def get_mode_config(self) -> dict:
        """Retourne la configuration du mode actuel"""
        return self._state.get_mode_config()

    def get_mode_history(self) -> List[dict]:
        """Retourne l'historique des changements de mode"""
        return self._mode_history

    def handle_presence_detected(self) -> None:
        """Delegue la gestion de presence a l'etat courant"""
        self._state.handle_presence_detected(self)

    def handle_night_time(self) -> None:
        """Delegue la gestion de l'heure de nuit a l'etat courant"""
        self._state.handle_night_time(self)

    def handle_day_time(self) -> None:
        """Delegue la gestion de l'heure de jour a l'etat courant"""
        self._state.handle_day_time(self)
