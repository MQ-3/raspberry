from datetime import datetime

from db import get_connection


def serialize_short(row):
    unlocked_at = row.get("unlocked_at")
    if isinstance(unlocked_at, datetime):
        unlocked_at = unlocked_at.strftime("%Y-%m-%d %H:%M:%S")
    elif unlocked_at:
        unlocked_at = str(unlocked_at)[:19]

    watched_at = row.get("watched_at")
    if isinstance(watched_at, datetime):
        watched_at = watched_at.strftime("%Y-%m-%d %H:%M:%S")
    elif watched_at:
        watched_at = str(watched_at)[:19]

    return {
        "episode_no": row["episode_no"],
        "title": row["title"],
        "video_path": row["video_path"],
        "is_unlocked": bool(row.get("is_unlocked", 0)),
        "unlocked_at": unlocked_at,
        "is_watched": bool(row.get("is_watched", 0)),
        "watched_at": watched_at,
    }


def _ensure_ep1_unlocked(user_id):
    """유저 최초 접근 시 EP.1 자동 잠금 해제"""
    conn = get_connection()
    try:
        with conn.cursor() as cursor:
            cursor.execute(
                "SELECT COUNT(*) as cnt FROM user_shorts_progress WHERE user_id = %s",
                (user_id,),
            )
            row = cursor.fetchone()
            if row["cnt"] == 0:
                cursor.execute(
                    """
                    INSERT OR IGNORE INTO user_shorts_progress (user_id, episode_no, is_unlocked, unlocked_at)
                    VALUES (%s, 1, 1, %s)
                    """,
                    (user_id, datetime.now()),
                )
        conn.commit()
    finally:
        conn.close()


def get_shorts(user_id):
    _ensure_ep1_unlocked(user_id)
    conn = get_connection()
    try:
        with conn.cursor() as cursor:
            cursor.execute(
                """
                SELECT s.episode_no, s.title, s.video_path,
                       COALESCE(p.is_unlocked, 0) AS is_unlocked,
                       p.unlocked_at,
                       COALESCE(p.is_watched, 0) AS is_watched,
                       p.watched_at
                FROM shorts s
                LEFT JOIN user_shorts_progress p
                    ON s.episode_no = p.episode_no AND p.user_id = %s
                ORDER BY s.episode_no ASC
                """,
                (user_id,),
            )
            rows = cursor.fetchall()
        return [serialize_short(row) for row in rows]
    finally:
        conn.close()


def get_next_locked_short(user_id):
    _ensure_ep1_unlocked(user_id)
    conn = get_connection()
    try:
        with conn.cursor() as cursor:
            cursor.execute(
                """
                SELECT s.episode_no, s.title, s.video_path,
                       COALESCE(p.is_unlocked, 0) AS is_unlocked,
                       p.unlocked_at,
                       COALESCE(p.is_watched, 0) AS is_watched,
                       p.watched_at
                FROM shorts s
                LEFT JOIN user_shorts_progress p
                    ON s.episode_no = p.episode_no AND p.user_id = %s
                WHERE COALESCE(p.is_unlocked, 0) = 0
                ORDER BY s.episode_no ASC
                LIMIT 1
                """,
                (user_id,),
            )
            row = cursor.fetchone()
        return serialize_short(row) if row else None
    finally:
        conn.close()


def unlock_short(episode_no, user_id):
    conn = get_connection()
    try:
        with conn.cursor() as cursor:
            cursor.execute(
                """
                INSERT INTO user_shorts_progress (user_id, episode_no, is_unlocked, unlocked_at)
                VALUES (%s, %s, 1, %s)
                ON CONFLICT(user_id, episode_no) DO UPDATE SET
                    is_unlocked = 1, unlocked_at = %s
                """,
                (user_id, episode_no, datetime.now(), datetime.now()),
            )
        conn.commit()
    finally:
        conn.close()


def mark_short_watched(episode_no, user_id):
    conn = get_connection()
    try:
        with conn.cursor() as cursor:
            cursor.execute(
                """
                UPDATE user_shorts_progress
                SET is_watched = 1, watched_at = %s
                WHERE user_id = %s AND episode_no = %s AND is_unlocked = 1
                """,
                (datetime.now(), user_id, episode_no),
            )
        conn.commit()
        return True
    finally:
        conn.close()


def unlock_next_short_if_allowed(state_level, user_id):
    if state_level == "danger":
        return {
            "unlocked": False,
            "episode": None,
            "message": "지금은 쉬어갈 타이밍입니다. 다음 숏츠는 잠시 후 확인해주세요.",
        }

    next_short = get_next_locked_short(user_id)
    if next_short is None:
        return {
            "unlocked": False,
            "episode": None,
            "message": "이미 모든 숏츠가 잠금해제되었습니다.",
        }

    unlock_short(next_short["episode_no"], user_id)

    if state_level == "caution":
        message = "다음 숏츠가 잠금해제되었습니다. 물을 마시면서 천천히 감상하세요."
    else:
        message = "다음 숏츠가 잠금해제되었습니다."

    return {
        "unlocked": True,
        "episode": {
            "episode_no": next_short["episode_no"],
            "title": next_short["title"],
            "video_path": next_short["video_path"],
        },
        "message": message,
    }
