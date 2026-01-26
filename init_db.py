#!/usr/bin/env python3
import sqlite3
import os

DB_NAME = "habitat_ift785.db"


def init_database():
    if os.path.exists(DB_NAME):
        print(f"Base existante detectee, suppression...")
        os.remove(DB_NAME)

    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    print(f"Creation de la base: {DB_NAME}")

    cursor.execute(
        """
        CREATE TABLE sensor_readings (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            sensor_id TEXT NOT NULL,
            location TEXT NOT NULL,
            type TEXT NOT NULL,
            value REAL,
            unit TEXT,
            timestamp TEXT NOT NULL,
            received_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    """
    )

    cursor.execute(
        """
        CREATE INDEX idx_location_type 
        ON sensor_readings(location, type)
    """
    )

    cursor.execute(
        """
        CREATE INDEX idx_timestamp 
        ON sensor_readings(timestamp DESC)
    """
    )

    cursor.execute(
        """
        CREATE INDEX idx_type 
        ON sensor_readings(type)
    """
    )

    conn.commit()
    conn.close()

    print("Tables creees: sensor_readings")
    print("Index crees: idx_location_type, idx_timestamp, idx_type")
    print(f"Base de donnees {DB_NAME} prete")


if __name__ == "__main__":
    init_database()
