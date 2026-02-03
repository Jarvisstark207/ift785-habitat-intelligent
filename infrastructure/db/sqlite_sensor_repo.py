from typing import List, Optional
from datetime import datetime, timedelta
from domain.models.sensor_reading import SensorReading
from domain.ports.sensor_reading_repo import SensorReadingRepository
from infrastructure.db.sqlite_connection import SQLiteConnection


class SQLiteSensorRepository(SensorReadingRepository):
    """Implémentation SQLite du repository"""

    def save(self, reading: SensorReading) -> None:
        """Sauvegarde une lecture dans SQLite"""
        conn = SQLiteConnection.get_connection()
        cursor = conn.cursor()

        cursor.execute("""
            INSERT INTO sensor_readings 
            (sensor_id, location, type, value, unit, timestamp)
            VALUES (?, ?, ?, ?, ?, ?)
        """, reading.to_db_tuple())

        conn.commit()
        conn.close()

    def find_recent(self, limit: int = 20) -> List[dict]:
        """Trouve les N dernières lectures"""
        conn = SQLiteConnection.get_connection()
        cursor = conn.cursor()

        cursor.execute("""
            SELECT * FROM sensor_readings
            ORDER BY timestamp DESC LIMIT ?
        """, (limit,))

        rows = cursor.fetchall()
        conn.close()

        return [dict(row) for row in rows]

    def find_by_location_and_type(
        self,
        location: str,
        sensor_type: str,
        limit: int = 10
    ) -> List[SensorReading]:
        """Trouve lectures par location et type"""
        conn = SQLiteConnection.get_connection()
        cursor = conn.cursor()

        cursor.execute("""
            SELECT sensor_id, location, type, value, unit, timestamp
            FROM sensor_readings
            WHERE location = ? AND type = ?
            ORDER BY timestamp DESC LIMIT ?
        """, (location, sensor_type, limit))

        rows = cursor.fetchall()
        conn.close()

        return [
            SensorReading(
                sensor_id=row[0],
                location=row[1],
                type=row[2],
                value=row[3],
                unit=row[4],
                timestamp=row[5]
            )
            for row in rows
        ]

    def find_temperature_history(self, locations: List[str]) -> dict:
        """Historique températures pour graphique"""
        conn = SQLiteConnection.get_connection()
        cursor = conn.cursor()

        history = {}

        for location in locations:
            cursor.execute("""
                SELECT value, timestamp FROM sensor_readings
                WHERE location = ? AND type = 'temperature'
                ORDER BY timestamp DESC LIMIT 10
            """, (location,))

            rows = cursor.fetchall()
            history[location] = [
                {'value': row[0], 'timestamp': row[1]}
                for row in reversed(rows)
            ]

        conn.close()
        return history

    def find_consumption_current(self, locations: List[str]) -> dict:
        """Consommation actuelle par location"""
        conn = SQLiteConnection.get_connection()
        cursor = conn.cursor()

        consumption = {}

        for location in locations:
            cursor.execute("""
                SELECT value FROM sensor_readings
                WHERE location = ? AND type = 'consommation'
                ORDER BY timestamp DESC LIMIT 1
            """, (location,))

            row = cursor.fetchone()
            consumption[location] = round(row[0], 1) if row else 0

        conn.close()
        return consumption

    def get_stats_for_location(self, location: str) -> dict:
        """Calcule les statistiques pour une location"""
        conn = SQLiteConnection.get_connection()
        cursor = conn.cursor()

        stats = {}

        # Température
        cursor.execute("""
            SELECT AVG(value), MIN(value), MAX(value)
            FROM (
                SELECT value FROM sensor_readings
                WHERE location = ? AND type = 'temperature'
                ORDER BY timestamp DESC LIMIT 10
            )
        """, (location,))
        row = cursor.fetchone()
        stats['temp_avg'] = round(row[0], 1) if row[0] else None
        stats['temp_min'] = round(row[1], 1) if row[1] else None
        stats['temp_max'] = round(row[2], 1) if row[2] else None

        # Luminosité
        cursor.execute("""
            SELECT value FROM sensor_readings
            WHERE location = ? AND type = 'lumiere'
            ORDER BY timestamp DESC LIMIT 1
        """, (location,))
        row = cursor.fetchone()
        stats['luminosity'] = int(row[0]) if row else None

        # Mouvement
        five_min_ago = (datetime.now() - timedelta(minutes=5)).isoformat()
        cursor.execute("""
            SELECT value FROM sensor_readings
            WHERE location = ? AND type = 'mouvement'
            AND timestamp > ?
            ORDER BY timestamp DESC LIMIT 1
        """, (location, five_min_ago))
        row = cursor.fetchone()
        stats['movement'] = bool(row[0]) if row else False

        # Consommation
        cursor.execute("""
            SELECT value FROM sensor_readings
            WHERE location = ? AND type = 'consommation'
            ORDER BY timestamp DESC LIMIT 1
        """, (location,))
        row = cursor.fetchone()
        stats['consumption'] = round(row[0], 1) if row else None

        conn.close()
        return stats

    def get_total_consumption(self, locations: List[str]) -> float:
        """Calcule consommation totale"""
        conn = SQLiteConnection.get_connection()
        cursor = conn.cursor()

        total = 0
        for location in locations:
            cursor.execute("""
                SELECT value FROM sensor_readings
                WHERE location = ? AND type = 'consommation'
                ORDER BY timestamp DESC LIMIT 1
            """, (location,))
            row = cursor.fetchone()
            if row and row[0]:
                total += row[0]

        conn.close()
        return round(total, 1)

    def get_occupied_rooms_count(self) -> int:
        """Compte pièces occupées"""
        conn = SQLiteConnection.get_connection()
        cursor = conn.cursor()

        five_min_ago = (datetime.now() - timedelta(minutes=5)).isoformat()
        cursor.execute("""
            SELECT COUNT(DISTINCT location) FROM sensor_readings
            WHERE type = 'mouvement' AND value = 1
            AND timestamp > ?
        """, (five_min_ago,))

        count = cursor.fetchone()[0]
        conn.close()
        return count

    def get_average_temperature(self, locations: List[str]) -> float:
        """Calcule température moyenne maison"""
        conn = SQLiteConnection.get_connection()
        cursor = conn.cursor()

        temps = []
        for location in locations:
            cursor.execute("""
                SELECT value FROM sensor_readings
                WHERE location = ? AND type = 'temperature'
                ORDER BY timestamp DESC LIMIT 1
            """, (location,))
            row = cursor.fetchone()
            if row and row[0]:
                temps.append(row[0])

        conn.close()
        return round(sum(temps) / len(temps), 1) if temps else None

    def find_with_filters(
            self,
            location: Optional[str] = None,
            sensor_type: Optional[str] = None,
            start_date: Optional[str] = None,
            end_date: Optional[str] = None,
            limit: int = 100
    ) -> List[dict]:
        """Trouve lectures avec filtres multiples"""
        conn = SQLiteConnection.get_connection()
        cursor = conn.cursor()

        query = "SELECT * FROM sensor_readings WHERE 1=1"
        params = []

        if location:
            query += " AND location = ?"
            params.append(location)

        if sensor_type:
            query += " AND type = ?"
            params.append(sensor_type)

        if start_date:
            query += " AND timestamp >= ?"
            params.append(start_date)

        if end_date:
            query += " AND timestamp <= ?"
            params.append(end_date)

        query += " ORDER BY timestamp DESC LIMIT ?"
        params.append(limit)

        cursor.execute(query, tuple(params))
        rows = cursor.fetchall()
        conn.close()

        return [dict(row) for row in rows]