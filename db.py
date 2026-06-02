from datetime import datetime

import pymysql
from pymysql.cursors import DictCursor

import config


def get_connection():
    return pymysql.connect(
        host=config.DB_HOST,
        user=config.DB_USER,
        password=config.DB_PASSWORD,
        database=config.DB_NAME,
        charset=config.DB_CHARSET,
        cursorclass=DictCursor,
        autocommit=False,
    )


def init_tables():
    conn = get_connection()
    try:
        with conn.cursor() as cursor:
            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS users (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    email VARCHAR(255) NOT NULL UNIQUE,
                    password_hash VARCHAR(255) NOT NULL,
                    created_at DATETIME NOT NULL
                )
                """
            )
            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS drink_logs (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    user_id INT,
                    measured_at DATETIME NOT NULL,
                    sensor_value INT NOT NULL,
                    state_level VARCHAR(20) NOT NULL,
                    state_label VARCHAR(50) NOT NULL,
                    state_message VARCHAR(255),
                    drink_type VARCHAR(50),
                    drink_amount FLOAT,
                    drink_unit VARCHAR(20),
                    memo VARCHAR(255),
                    FOREIGN KEY (user_id) REFERENCES users(id)
                )
                """
            )
            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS shorts (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    episode_no INT NOT NULL UNIQUE,
                    title VARCHAR(100) NOT NULL,
                    video_path VARCHAR(255) NOT NULL,
                    is_unlocked BOOLEAN DEFAULT FALSE,
                    unlocked_at DATETIME
                )
                """
            )
        conn.commit()
        seed_shorts()
    finally:
        conn.close()


def seed_shorts():
    rows = [
        (1, "EP.1 비밀 계약의 시작", "/static/videos/ep1.mp4", True, datetime.now()),
        (2, "EP.2 유전자 검사 결과", "/static/videos/ep2.mp4", False, None),
        (3, "EP.3 결혼식장의 배신", "/static/videos/ep3.mp4", False, None),
    ]

    conn = get_connection()
    try:
        with conn.cursor() as cursor:
            for row in rows:
                cursor.execute(
                    """
                    INSERT INTO shorts
                        (episode_no, title, video_path, is_unlocked, unlocked_at)
                    VALUES (%s, %s, %s, %s, %s)
                    ON DUPLICATE KEY UPDATE
                        title = VALUES(title),
                        video_path = VALUES(video_path)
                    """,
                    row,
                )
        conn.commit()
    finally:
        conn.close()


if __name__ == "__main__":
    init_tables()
    print("Database tables are ready.")
