"""Modeles de scenarios automatises"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import List
import uuid


@dataclass
class ScenarioCondition:
    """Condition declencheur d'un scenario"""

    trigger_type: str  # temperature, motion, time, luminosity
    operator: str  # >, <, ==, >=, <=
    value: float

    def evaluate(self, event_value: float) -> bool:
        """Evalue si la condition est satisfaite"""
        ops = {
            ">": lambda a, b: a > b,
            "<": lambda a, b: a < b,
            "==": lambda a, b: a == b,
            ">=": lambda a, b: a >= b,
            "<=": lambda a, b: a <= b,
        }
        op_func = ops.get(self.operator)
        return op_func(event_value, self.value) if op_func else False

    def to_dict(self) -> dict:
        return {
            "trigger_type": self.trigger_type,
            "operator": self.operator,
            "value": self.value,
        }


@dataclass
class ScenarioAction:
    """Action executee par un scenario"""

    device_id: str
    action: str
    parameters: dict = field(default_factory=dict)

    def to_dict(self) -> dict:
        return {
            "device_id": self.device_id,
            "action": self.action,
            "parameters": self.parameters,
        }


@dataclass
class Scenario:
    """Scenario automatise - regle 'Si condition alors actions'"""

    name: str
    conditions: List[ScenarioCondition]
    actions: List[ScenarioAction]
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    is_active: bool = True
    description: str = ""
    execution_log: List[dict] = field(default_factory=list)
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())

    def execute(self) -> dict:
        """Execute le scenario et enregistre l'activation"""
        entry = {
            "executed_at": datetime.now().isoformat(),
            "actions_count": len(self.actions),
            "status": "executed",
        }
        self.execution_log.append(entry)
        return {
            "scenario_id": self.id,
            "scenario_name": self.name,
            "executed_at": entry["executed_at"],
            "actions_executed": [a.to_dict() for a in self.actions],
        }

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "is_active": self.is_active,
            "conditions": [c.to_dict() for c in self.conditions],
            "actions": [a.to_dict() for a in self.actions],
            "execution_count": len(self.execution_log),
            "created_at": self.created_at,
        }
