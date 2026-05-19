from datetime import datetime

from db import get_connection


def serialize_short(row):
    return {
        "episode_no": row["episode_no"],
        "title": row["title"],
        "video_path": row["video_path"],
        "is_unlocked": bool(row["is_unlocked"]),
        "unlocked_at": row["unlocked_at"].strftime("%Y-%m-%d %H:%M:%S") if row.get("unlocked_at") else None,
    }


def get_shorts():
    conn = get_connection()
    try:
        with conn.cursor() as cursor:
            cursor.execute(
                """
                SELECT episode_no, title, video_path, is_unlocked, unlocked_at
                FROM shorts
                ORDER BY episode_no ASC
                """
            )
            rows = cursor.fetchall()
        return [serialize_short(row) for row in rows]
    finally:
        conn.close()


def get_next_locked_short():
    conn = get_connection()
    try:
        with conn.cursor() as cursor:
            cursor.execute(
                """
                SELECT episode_no, title, video_path, is_unlocked, unlocked_at
                FROM shorts
                WHERE is_unlocked = FALSE
                ORDER BY episode_no ASC
                LIMIT 1
                """
            )
            row = cursor.fetchone()
        return serialize_short(row) if row else None
    finally:
        conn.close()


def unlock_short(episode_no):
    conn = get_connection()
    try:
        with conn.cursor() as cursor:
            cursor.execute(
                """
                UPDATE shorts
                SET is_unlocked = TRUE, unlocked_at = %s
                WHERE episode_no = %s
                """,
                (datetime.now(), episode_no),
            )
        conn.commit()
    finally:
        conn.close()


def unlock_next_short_if_allowed(state_level):
    if state_level == "danger":
        return {
            "unlocked": False,
            "episode": None,
            "message": "지금은 쉬어갈 타이밍입니다. 다음 숏츠는 잠시 후 확인해주세요.",
        }

    next_short = get_next_locked_short()
    if next_short is None:
        return {
            "unlocked": False,
            "episode": None,
            "message": "이미 모든 숏츠가 잠금해제되었습니다.",
        }

    unlock_short(next_short["episode_no"])

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
