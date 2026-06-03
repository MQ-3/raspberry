from datetime import date, datetime, time, timedelta

from db import get_connection
from state import get_state_color, get_state_priority


def format_datetime(value):
    if value is None:
        return None
    if isinstance(value, datetime):
        return value.strftime("%Y-%m-%d %H:%M:%S")
    return str(value)


def format_date(value):
    if value is None:
        return None
    if isinstance(value, date):
        return value.strftime("%Y-%m-%d")
    return str(value)


def serialize_log(row):
    return {
        "id": row["id"],
        "measured_at": format_datetime(row["measured_at"]),
        "sensor_value": row["sensor_value"],
        "state_level": row["state_level"],
        "state_label": row["state_label"],
        "state_message": row.get("state_message"),
        "drink_type": row.get("drink_type"),
        "drink_amount": row.get("drink_amount"),
        "drink_unit": row.get("drink_unit"),
        "memo": row.get("memo"),
    }


def _get_tolerance_and_bottles(user_id):
    """(tolerance, total_bottles) 반환. user_id 없거나 tolerance 미설정이면 (None, 0.0)."""
    if not user_id:
        return None, 0.0

    conn = get_connection()
    try:
        with conn.cursor() as cursor:
            cursor.execute(
                "SELECT alcohol_tolerance FROM users WHERE id = %s", (user_id,)
            )
            row = cursor.fetchone()
        if not row or row["alcohol_tolerance"] is None:
            return None, 0.0
        tolerance = row["alcohol_tolerance"]

        today = date.today()
        start = datetime.combine(today, time.min)
        end = start + timedelta(days=1)

        with conn.cursor() as cursor:
            cursor.execute(
                """
                SELECT drink_type, drink_unit, SUM(drink_amount) AS total
                FROM drink_logs
                WHERE user_id = %s AND measured_at >= %s AND measured_at < %s
                  AND drink_type IS NOT NULL
                GROUP BY drink_type, drink_unit
                """,
                (user_id, start, end),
            )
            rows = cursor.fetchall()
    finally:
        conn.close()

    total_bottles = 0.0
    for r in rows:
        amount = r["total"] or 0
        if r["drink_type"] == "소주" and r["drink_unit"] == "잔":
            total_bottles += amount / 8
        elif r["drink_type"] == "맥주" and r["drink_unit"] == "캔":
            total_bottles += amount / 2.4

    return tolerance, total_bottles


def calc_today_exceeded(user_id):
    """오늘 음주 기록을 소주 병수로 환산해 주량 초과 여부를 반환한다."""
    tolerance, total_bottles = _get_tolerance_and_bottles(user_id)
    if tolerance is None:
        return False
    return total_bottles > tolerance


def calc_heavy_drinking(user_id):
    """주량 + 반병(0.5) 초과 시 과음으로 판단한다."""
    tolerance, total_bottles = _get_tolerance_and_bottles(user_id)
    if tolerance is None:
        return False
    return total_bottles > tolerance + 0.5


def save_drink_log(data):
    measured_at = data.get("measured_at") or datetime.now()

    conn = get_connection()
    try:
        with conn.cursor() as cursor:
            cursor.execute(
                """
                INSERT INTO drink_logs (
                    user_id, measured_at, sensor_value, state_level, state_label,
                    state_message, drink_type, drink_amount, drink_unit, memo
                )
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                """,
                (
                    data.get("user_id"),
                    measured_at,
                    data["sensor_value"],
                    data["state_level"],
                    data["state_label"],
                    data.get("state_message"),
                    data.get("drink_type"),
                    data.get("drink_amount"),
                    data.get("drink_unit"),
                    data.get("memo"),
                ),
            )
            log_id = cursor.lastrowid
        conn.commit()
        return log_id
    finally:
        conn.close()


def get_today_logs(user_id=None):
    today = date.today()
    start = datetime.combine(today, time.min)
    end = start + timedelta(days=1)
    return get_logs_between(start, end, user_id=user_id)


def get_logs_between(start, end, user_id=None):
    conn = get_connection()
    try:
        with conn.cursor() as cursor:
            if user_id:
                cursor.execute(
                    """
                    SELECT *
                    FROM drink_logs
                    WHERE measured_at >= %s AND measured_at < %s AND user_id = %s
                    ORDER BY measured_at ASC
                    """,
                    (start, end, user_id),
                )
            else:
                cursor.execute(
                    """
                    SELECT *
                    FROM drink_logs
                    WHERE measured_at >= %s AND measured_at < %s
                    ORDER BY measured_at ASC
                    """,
                    (start, end),
                )
            rows = cursor.fetchall()
        return [serialize_log(row) for row in rows]
    finally:
        conn.close()


def get_week_report(user_id=None):  # 새로 추가: user_id 파라미터
    today = date.today()
    week_start = today - timedelta(days=today.weekday())
    week_end = week_start + timedelta(days=7)
    return {
        "start_date": week_start.strftime("%Y-%m-%d"),
        "end_date": (week_end - timedelta(days=1)).strftime("%Y-%m-%d"),
        "days": get_daily_summary(week_start, week_end, user_id=user_id),
    }


def get_month_report(year=None, month=None, user_id=None):  # 새로 추가: user_id 파라미터
    today = date.today()
    year = year or today.year
    month = month or today.month

    start = date(year, month, 1)
    if month == 12:
        end = date(year + 1, 1, 1)
    else:
        end = date(year, month + 1, 1)

    return {
        "year": year,
        "month": month,
        "days": get_daily_summary(start, end, user_id=user_id),
    }


def get_daily_summary(start_date, end_date, user_id=None):  # 새로 추가: user_id 파라미터
    conn = get_connection()
    try:
        with conn.cursor() as cursor:
            # 새로 추가: user_id 있으면 해당 유저 데이터만 조회
            if user_id:
                cursor.execute(
                    """
                    SELECT
                        DATE(measured_at) AS log_date,
                        state_level,
                        MAX(sensor_value) AS max_value
                    FROM drink_logs
                    WHERE measured_at >= %s AND measured_at < %s AND user_id = %s
                    GROUP BY DATE(measured_at), state_level
                    ORDER BY log_date ASC
                    """,
                    (start_date, end_date, user_id),
                )
            else:
                cursor.execute(
                    """
                    SELECT
                        DATE(measured_at) AS log_date,
                        state_level,
                        MAX(sensor_value) AS max_value
                    FROM drink_logs
                    WHERE measured_at >= %s AND measured_at < %s
                    GROUP BY DATE(measured_at), state_level
                    ORDER BY log_date ASC
                    """,
                    (start_date, end_date),
                )
            rows = cursor.fetchall()
    finally:
        conn.close()

    by_date = {}
    for row in rows:
        log_date = format_date(row["log_date"])
        state_level = row["state_level"]
        candidate = {
            "date": log_date,
            "state_level": state_level,
            "color": get_state_color(state_level),
            "max_value": row["max_value"],
        }

        current = by_date.get(log_date)
        if current is None:
            by_date[log_date] = candidate
            continue

        if get_state_priority(state_level) > get_state_priority(current["state_level"]):
            by_date[log_date] = candidate
        elif candidate["max_value"] > current["max_value"]:
            by_date[log_date]["max_value"] = candidate["max_value"]

    return list(by_date.values())
