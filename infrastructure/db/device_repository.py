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

    def find_by_type(self, device_type: str) -> List[DeviceRecord]:
        """Recherche les devices par type"""
        return self.session.query(DeviceRecord).filter_by(
            device_type=device_type
        ).all()

    def find_by_room(self, room_name: str) -> List[DeviceRecord]:
        """Recherche les devices par piece"""
        return self.session.query(DeviceRecord).filter_by(
            room_name=room_name
        ).all()

    def delete(self, device_id: str) -> bool:
        """Supprime un device par son identifiant"""
        device = self.find_by_id(device_id)
        if device:
            self.session.delete(device)
            return True
        return False

    def count(self) -> int:
        """Retourne le nombre total de devices"""
        return self.session.query(DeviceRecord).count()
