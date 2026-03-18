"""
Modeles SQLAlchemy pour l'iteration 6 - Repository Pattern + Unit of Work
"""

from sqlalchemy import Column, String, Float, Integer, Text
from sqlalchemy.orm import declarative_base

Base = declarative_base()


class DeviceRecord(Base):
    """Modele SQLAlchemy pour persister les devices"""

    __tablename__ = "devices"

    device_id = Column(String, primary_key=True)
    name = Column(String, nullable=False)
    room_name = Column(String, default="")
    device_type = Column(String, default="")
    manufacturer = Column(String, default="")
    status = Column(String, default="active")
    properties = Column(Text, default="{}")

    def to_dict(self):
        return {
            "device_id": self.device_id,
            "name": self.name,
            "room_name": self.room_name,
            "device_type": self.device_type,
            "manufacturer": self.manufacturer,
            "status": self.status,
        }


class SensorReadingRecord(Base):
    """Modele SQLAlchemy pour les lectures de capteurs"""

    __tablename__ = "sensor_readings_v2"

    id = Column(Integer, primary_key=True, autoincrement=True)
    sensor_id = Column(String, nullable=False)
    location = Column(String, nullable=False)
    type = Column(String, nullable=False)
    value = Column(Float, nullable=False)
    unit = Column(String, nullable=False)
    timestamp = Column(String, nullable=False)

    def to_dict(self):
        return {
            "id": self.id,
            "sensor_id": self.sensor_id,
            "location": self.location,
            "type": self.type,
            "value": self.value,
            "unit": self.unit,
            "timestamp": self.timestamp,
        }
