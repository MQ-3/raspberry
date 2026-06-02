from db import get_connection


def register_user(email: str, password: str) -> dict:
    conn = get_connection()
    try:
        with conn.cursor() as cursor:
            cursor.execute("SELECT id FROM users WHERE email = %s", (email,))
            if cursor.fetchone():
                raise ValueError("이미 사용 중인 이메일입니다")

            cursor.execute(
                "INSERT INTO users (email, password) VALUES (%s, %s)",
                (email, password),
            )
            user_id = cursor.lastrowid
        conn.commit()
    finally:
        conn.close()

    return {"user_id": user_id, "email": email}


def login_user(email: str, password: str) -> dict:
    conn = get_connection()
    try:
        with conn.cursor() as cursor:
            cursor.execute(
                "SELECT id, email FROM users WHERE email = %s AND password = %s",
                (email, password),
            )
            user = cursor.fetchone()
    finally:
        conn.close()

    if not user:
        raise ValueError("이메일 또는 비밀번호가 올바르지 않습니다")

    return {"user_id": user["id"], "email": user["email"]}


def delete_user(user_id: int) -> None:
    conn = get_connection()
    try:
        with conn.cursor() as cursor:
            cursor.execute("SELECT id FROM users WHERE id = %s", (user_id,))
            if not cursor.fetchone():
                raise ValueError("존재하지 않는 사용자입니다")

            cursor.execute("DELETE FROM users WHERE id = %s", (user_id,))
        conn.commit()
    finally:
        conn.close()
