"""
Unit of Work Pattern - Iteration 6
Gestion des transactions avec rollback atomique
"""

from infrastructure.db.device_repository import DeviceRepository
from infrastructure.db.sqlalchemy_session import get_default_session_factory


class SQLAlchemyUnitOfWork:
    """
    Unite de travail SQLAlchemy.
    Garantit que toutes les operations dans un bloc sont atomiques.
    Utilisation : with SQLAlchemyUnitOfWork(factory) as uow:
                      uow.devices.save(...)
                      uow.commit()
    """

    def __init__(self, session_factory=None):
        if session_factory is None:
            session_factory = get_default_session_factory()
        self.session_factory = session_factory
        self.session = None
        self.devices = None

    def __enter__(self):
        self.session = self.session_factory()
        self.devices = DeviceRepository(self.session)
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if exc_type:
            self.rollback()
        self.session.close()
        return False

    def commit(self):
        """Valide toutes les operations de l'unite de travail"""
        self.session.commit()

    def rollback(self):
        """Annule toutes les operations de l'unite de travail"""
        self.session.rollback()
