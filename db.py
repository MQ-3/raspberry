import os
import sqlite3
from datetime import datetime

DB_PATH = os.path.join(os.path.dirname(__file__), 'sulchingu.db')


class _Cursor:
    def __init__(self, cursor):
        self._c = cursor

    def execute(self, sql, params=()):
        sql = sql.replace('%s', '?')
        params = tuple(
            p.strftime('%Y-%m-%d %H:%M:%S') if isinstance(p, datetime) else p
            for p in params
        )
        self._c.execute(sql, params)

    def fetchone(self):
        row = self._c.fetchone()
        return dict(row) if row else None

    def fetchall(self):
        return [dict(row) for row in self._c.fetchall()]

    @property
    def lastrowid(self):
        return self._c.lastrowid

    @property
    def rowcount(self):
        return self._c.rowcount

    def __enter__(self):
        return self

    def __exit__(self, *args):
        pass


class _Connection:
    def __init__(self, conn):
        self._conn = conn

    def cursor(self):
        return _Cursor(self._conn.cursor())

    def commit(self):
        self._conn.commit()

    def close(self):
        self._conn.close()


def get_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return _Connection(conn)


def _add_column_if_missing(cursor, table, col, definition):
    try:
        cursor.execute(f"ALTER TABLE {table} ADD COLUMN {col} {definition}")
    except Exception:
        pass


def init_tables():
    conn = get_connection()
    try:
        with conn.cursor() as cursor:
            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS users (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    email TEXT NOT NULL UNIQUE,
                    password_hash TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    weight REAL,
                    gender TEXT,
                    alcohol_tolerance TEXT
                )
                """
            )
            _add_column_if_missing(cursor, 'users', 'weight', 'REAL')
            _add_column_if_missing(cursor, 'users', 'gender', 'TEXT')
            _add_column_if_missing(cursor, 'users', 'alcohol_tolerance', 'TEXT')
            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS drink_logs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER,
                    measured_at TEXT NOT NULL,
                    sensor_value INTEGER NOT NULL,
                    state_level TEXT NOT NULL,
                    state_label TEXT NOT NULL,
                    state_message TEXT,
                    drink_type TEXT,
                    drink_amount REAL,
                    drink_unit TEXT,
                    memo TEXT
                )
                """
            )
            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS shorts (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    episode_no INTEGER NOT NULL UNIQUE,
                    title TEXT NOT NULL,
                    video_path TEXT NOT NULL,
                    is_unlocked INTEGER DEFAULT 0,
                    unlocked_at TEXT
                )
                """
            )
        conn.commit()
        seed_shorts()
    finally:
        conn.close()


def seed_shorts():
    rows = [
        (1, "EP.1 비밀 계약의 시작", "/static/videos/ep1.mp4", 1, datetime.now().strftime('%Y-%m-%d %H:%M:%S')),
        (2, "EP.2 유전자 검사 결과", "/static/videos/ep2.mp4", 0, None),
        (3, "EP.3 결혼식장의 배신", "/static/videos/ep3.mp4", 0, None),
    ]

    conn = get_connection()
    try:
        with conn.cursor() as cursor:
            for row in rows:
                cursor.execute(
                    """
                    INSERT INTO shorts (episode_no, title, video_path, is_unlocked, unlocked_at)
                    VALUES (%s, %s, %s, %s, %s)
                    ON CONFLICT(episode_no) DO UPDATE SET
                        title=excluded.title,
                        video_path=excluded.video_path
                    """,
                    row,
                )
        conn.commit()
    finally:
        conn.close()


if __name__ == "__main__":
    init_tables()
    print("Database tables are ready.")
