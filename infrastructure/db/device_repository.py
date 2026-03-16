"""
Repository Pattern pour les devices - Iteration 6
Abstraction de l'acces aux donnees avec SQLAlchemy
"""

from typing import List, Optional
from infrastructure.db.sqlalchemy_models import DeviceRecord


class DeviceRepository:
    """Repository pour la persistance des devices via SQLAlchemy"""

    def __init__(self, session):
        self.session = session

    def save(self, device: DeviceRecord) -> DeviceRecord:
        """Persiste un device (insert ou update)"""
        existing = self.find_by_id(device.device_id)
        if existing:
            existing.name = device.name
            existing.room_name = device.room_name
            existing.device_type = device.device_type
            existing.manufacturer = device.manufacturer
            existing.status = device.status
            existing.properties = device.properties
            return existing
        self.session.add(device)
        return device

    def find_by_id(self, device_id: str) -> Optional[DeviceRecord]:
        """Recherche un device par son identifiant"""
        return self.session.query(DeviceRecord).filter_by(
            device_id=device_id
        ).first()

    def find_all(self) -> List[DeviceRecord]:
        """Retourne tous les devices"""
        return self.session.query(DeviceRecord).all()
