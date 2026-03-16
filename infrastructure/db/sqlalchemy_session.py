"""
Fabrique de sessions SQLAlchemy pour l'iteration 6
"""

import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from infrastructure.db.sqlalchemy_models import Base
import config

# Chemin absolu du projet (2 niveaux au-dessus de ce fichier)
_PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def create_session_factory(db_url: str = None):
    """Cree et retourne une fabrique de sessions SQLAlchemy"""
    if db_url is None:
        db_path = os.path.join(_PROJECT_ROOT, config.DB_NAME)
        db_url = f"sqlite:///{db_path}"
    engine = create_engine(db_url, connect_args={"check_same_thread": False})
    Base.metadata.create_all(engine)
    return sessionmaker(bind=engine, autocommit=False, autoflush=False)

