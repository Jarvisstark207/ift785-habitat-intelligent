"""Etats concrets de la maison - Pattern State"""

from domain.patterns.state import HouseState


class DomicileState(HouseState):
    """Mode domicile: presence detectee, fonctionnalites normales actives"""

    def on_enter(self, house) -> None:
        house.log_event("Entree en mode Domicile")

    def on_exit(self, house) -> None:
        house.log_event("Sortie du mode Domicile")

    def handle_presence_detected(self, house) -> None:
        pass  # deja en mode domicile

    def handle_night_time(self, house) -> None:
        house.set_state(NuitState())

    def handle_day_time(self, house) -> None:
        pass  # deja en mode domicile le jour

    def get_mode_name(self) -> str:
        return "domicile"

    def get_mode_config(self) -> dict:
        return {
            "lights_corridor": 100,
            "sound_notifications": True,
            "motion_alerts": False,
            "security_max": False,
        }


class NuitState(HouseState):
    """Mode nuit (22h-6h): lumieres reduites, pas de notifications sonores"""

    def on_enter(self, house) -> None:
        house.log_event("Entree en mode Nuit")

    def on_exit(self, house) -> None:
        house.log_event("Sortie du mode Nuit")

    def handle_presence_detected(self, house) -> None:
        house.set_state(DomicileState())

    def handle_night_time(self, house) -> None:
        pass  # deja en mode nuit

    def handle_day_time(self, house) -> None:
        house.set_state(DomicileState())

    def get_mode_name(self) -> str:
        return "nuit"

    def get_mode_config(self) -> dict:
        return {
            "lights_corridor": 10,
            "sound_notifications": False,
            "motion_alerts": True,
            "security_max": False,
        }


class AbsenceState(HouseState):
    """Mode absence: pas de presence, alertes actives"""

    def on_enter(self, house) -> None:
        house.log_event("Entree en mode Absence")

    def on_exit(self, house) -> None:
        house.log_event("Sortie du mode Absence")

    def handle_presence_detected(self, house) -> None:
        house.set_state(DomicileState())

    def handle_night_time(self, house) -> None:
        pass  # reste en absence la nuit

    def handle_day_time(self, house) -> None:
        pass  # reste en absence le jour

    def get_mode_name(self) -> str:
        return "absence"

    def get_mode_config(self) -> dict:
        return {
            "lights_corridor": 0,
            "sound_notifications": False,
            "motion_alerts": True,
            "security_max": True,
        }


class VacancesState(HouseState):
    """Mode vacances: simulation de presence, alertes securite maximales"""

    def on_enter(self, house) -> None:
        house.log_event("Entree en mode Vacances")

    def on_exit(self, house) -> None:
        house.log_event("Sortie du mode Vacances")

    def handle_presence_detected(self, house) -> None:
        house.log_event("Alerte securite: presence inattendue en mode Vacances")

    def handle_night_time(self, house) -> None:
        pass  # reste en vacances

    def handle_day_time(self, house) -> None:
        pass  # reste en vacances

    def get_mode_name(self) -> str:
        return "vacances"

    def get_mode_config(self) -> dict:
        return {
            "lights_corridor": 0,
            "sound_notifications": False,
            "motion_alerts": True,
            "security_max": True,
            "presence_simulation": True,
            "cameras_active": True,
            "email_alerts": True,
        }


MODE_STATE_MAP = {
    "domicile": DomicileState,
    "nuit": NuitState,
    "absence": AbsenceState,
    "vacances": VacancesState,
}


def get_state_for_mode(mode_name: str) -> HouseState:
    """Retourne l'etat correspondant au mode donne"""
    state_class = MODE_STATE_MAP.get(mode_name)
    if state_class is None:
        raise ValueError(f"Mode inconnu: {mode_name}")
    return state_class()
