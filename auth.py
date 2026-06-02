from datetime import datetime

from werkzeug.security import check_password_hash, generate_password_hash

from db import get_connection


def register_user(email, password):
    if len(password) < 6:
        raise ValueError("비밀번호는 6자 이상이어야 합니다.")

    password_hash = generate_password_hash(password)
    conn = get_connection()
    try:
        with conn.cursor() as cursor:
            cursor.execute("SELECT id FROM users WHERE email = %s", (email,))
            if cursor.fetchone():
                raise ValueError("이미 사용 중인 이메일입니다.")

            cursor.execute(
                "INSERT INTO users (email, password_hash, created_at) VALUES (%s, %s, %s)",
                (email, password_hash, datetime.now()),
            )
            user_id = cursor.lastrowid
        conn.commit()
        return {"id": user_id, "email": email}
    finally:
        conn.close()


def login_user(email, password):
    conn = get_connection()
    try:
        with conn.cursor() as cursor:
            cursor.execute(
                "SELECT id, email, password_hash FROM users WHERE email = %s", (email,)
            )
            user = cursor.fetchone()
        if not user or not check_password_hash(user["password_hash"], password):
            raise ValueError("이메일 또는 비밀번호가 올바르지 않습니다.")
        return {"id": user["id"], "email": user["email"]}
    finally:
        conn.close()


def delete_user(user_id):
    conn = get_connection()
    try:
        with conn.cursor() as cursor:
            cursor.execute("SELECT id FROM users WHERE id = %s", (user_id,))
            if not cursor.fetchone():
                raise ValueError("존재하지 않는 사용자입니다.")
            cursor.execute("DELETE FROM drink_logs WHERE user_id = %s", (user_id,))
            cursor.execute("DELETE FROM users WHERE id = %s", (user_id,))
        conn.commit()
    finally:
        conn.close()
