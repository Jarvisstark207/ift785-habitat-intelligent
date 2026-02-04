import sqlite3
from config import DB_NAME


class SQLiteConnection:
    """Factory pour connexions SQLite"""

    @staticmethod
    def get_connection():
        """Retourne une connexion SQLite configurée"""
        conn = sqlite3.connect(DB_NAME)
        conn.row_factory = sqlite3.Row
        return conn
