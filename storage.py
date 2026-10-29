"""
Data persistence layer using Repository pattern with SQLite.
"""

import os
import json
import sqlite3
import pandas as pd
from datetime import datetime
from typing import List, Dict, Any, Optional

class BaseRepository:
    def get_locations(self, discipline: Optional[str] = None) -> pd.DataFrame: raise NotImplementedError
    def get_providers(self, location_id: Optional[str] = None) -> pd.DataFrame: raise NotImplementedError
    def get_services(self, discipline: Optional[str] = None) -> pd.DataFrame: raise NotImplementedError
    def get_bookings(self, location_id: Optional[str] = None) -> pd.DataFrame: raise NotImplementedError
    def get_booking_by_id(self, booking_id: str) -> Optional[Dict[str, Any]]: raise NotImplementedError
    def get_bookings_by_phone(self, phone: str) -> List[Dict[str, Any]]: raise NotImplementedError
    def add_booking(self, booking: Dict[str, Any]) -> bool: raise NotImplementedError
    def update_booking(self, booking_id: str, updates: Dict[str, Any]) -> bool: raise NotImplementedError
    def get_holidays(self) -> pd.DataFrame: raise NotImplementedError

class SQLiteRepository(BaseRepository):
    def __init__(self, db_path: str = "appointment_agent/data/appointments.db"):
        self.db_path = db_path
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
        self._init_db()
        self._seed_sample_data()

    def _get_conn(self):
        return sqlite3.connect(self.db_path)

    def _init_db(self):
        with self._get_conn() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS locations (
                    location_id TEXT PRIMARY KEY, discipline TEXT, name TEXT,
                    address TEXT, lat REAL, lng REAL, phone TEXT, open_hours TEXT
                )
            """)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS providers (
                    provider_id TEXT PRIMARY KEY, location_id TEXT, name TEXT,
                    specialty TEXT, working_days TEXT, start_time TEXT, end_time TEXT,
                    break_start TEXT, break_end TEXT, active INTEGER
                )
            """)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS services (
                    service_id TEXT PRIMARY KEY, discipline TEXT, name TEXT, duration_min INTEGER
                )
            """)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS bookings (
                    booking_id TEXT PRIMARY KEY, discipline TEXT, location_id TEXT,
                    provider_id TEXT, service_id TEXT, customer_name TEXT, phone TEXT,
                    email TEXT, date TEXT, start_time TEXT, end_time TEXT, status TEXT,
                    channel_pref TEXT, extra_fields TEXT, created_at TEXT, updated_at TEXT
                )
            """)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS holidays (
                    holiday_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    target_id TEXT, date TEXT, reason TEXT
                )
            """)
            conn.commit()

    def _seed_sample_data(self):
        with self._get_conn() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM locations")
            if cursor.fetchone()[0] == 0:
                for filename, table in [
                    ("appointment_agent/data/sample_locations.csv", "locations"),
                    ("appointment_agent/data/sample_providers.csv", "providers"),
                    ("appointment_agent/data/sample_services.csv", "services"),
                ]:
                    if os.path.exists(filename):
                        df = pd.read_csv(filename)
                        df.to_sql(table, conn, if_exists="append", index=False)

    def get_locations(self, discipline: Optional[str] = None) -> pd.DataFrame:
        query = "SELECT * FROM locations"
        params = []
        if discipline:
            query += " WHERE discipline = ?"
            params.append(discipline)
        with self._get_conn() as conn:
            return pd.read_sql_query(query, conn, params=params)

    def get_providers(self, location_id: Optional[str] = None) -> pd.DataFrame:
        query = "SELECT * FROM providers WHERE active = 1"
        params = []
        if location_id:
            query += " AND location_id = ?"
            params.append(location_id)
        with self._get_conn() as conn:
            return pd.read_sql_query(query, conn, params=params)

    def get_services(self, discipline: Optional[str] = None) -> pd.DataFrame:
        query = "SELECT * FROM services"
        params = []
        if discipline:
            query += " WHERE discipline = ?"
            params.append(discipline)
        with self._get_conn() as conn:
            return pd.read_sql_query(query, conn, params=params)

    def get_bookings(self, location_id: Optional[str] = None) -> pd.DataFrame:
        query = "SELECT * FROM bookings"
        params = []
        if location_id:
            query += " WHERE location_id = ?"
            params.append(location_id)
        with self._get_conn() as conn:
            return pd.read_sql_query(query, conn, params=params)

    def get_booking_by_id(self, booking_id: str) -> Optional[Dict[str, Any]]:
        with self._get_conn() as conn:
            df = pd.read_sql_query("SELECT * FROM bookings WHERE booking_id = ?", conn, params=[booking_id])
            if not df.empty:
                res = df.iloc[0].to_dict()
                res["extra_fields"] = json.loads(res.get("extra_fields") or "{}")
                return res
        return None

    def get_bookings_by_phone(self, phone: str) -> List[Dict[str, Any]]:
        with self._get_conn() as conn:
            df = pd.read_sql_query("SELECT * FROM bookings WHERE phone = ?", conn, params=[phone])
            results = []
            for _, row in df.iterrows():
                d = row.to_dict()
                d["extra_fields"] = json.loads(d.get("extra_fields") or "{}")
                results.append(d)
            return results

    def add_booking(self, booking: Dict[str, Any]) -> bool:
        now = datetime.now().isoformat()
        extra = json.dumps(booking.get("extra_fields", {}))
        with self._get_conn() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO bookings (
                    booking_id, discipline, location_id, provider_id, service_id,
                    customer_name, phone, email, date, start_time, end_time,
                    status, channel_pref, extra_fields, created_at, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                booking["booking_id"], booking["discipline"], booking["location_id"],
                booking["provider_id"], booking["service_id"], booking["customer_name"],
                booking["phone"], booking["email"], booking["date"], booking["start_time"],
                booking["end_time"], booking["status"], booking["channel_pref"],
                extra, now, now
            ))
            conn.commit()
            return True

    def update_booking(self, booking_id: str, updates: Dict[str, Any]) -> bool:
        now = datetime.now().isoformat()
        fields = []
        values = []
        for k, v in updates.items():
            if k == "extra_fields":
                v = json.dumps(v)
            fields.append(f"{k} = ?")
            values.append(v)
        fields.append("updated_at = ?")
        values.append(now)
        values.append(booking_id)

        sql = f"UPDATE bookings SET {', '.join(fields)} WHERE booking_id = ?"
        with self._get_conn() as conn:
            cursor = conn.cursor()
            cursor.execute(sql, values)
            conn.commit()
            return cursor.rowcount > 0

    def get_holidays(self) -> pd.DataFrame:
        with self._get_conn() as conn:
            return pd.read_sql_query("SELECT * FROM holidays", conn)

def get_repository(st_secrets: Optional[Any] = None) -> BaseRepository:
    return SQLiteRepository()
