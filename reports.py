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


def save_drink_log(data):
    measured_at = data.get("measured_at") or datetime.now()

    conn = get_connection()
    try:
        with conn.cursor() as cursor:
            cursor.execute(
                """
                INSERT INTO drink_logs (
                    measured_at, sensor_value, state_level, state_label,
                    state_message, drink_type, drink_amount, drink_unit, memo
                )
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                """,
                (
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


def get_today_logs():
    today = date.today()
    start = datetime.combine(today, time.min)
    end = start + timedelta(days=1)
    return get_logs_between(start, end)


def get_logs_between(start, end):
    conn = get_connection()
    try:
        with conn.cursor() as cursor:
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


def get_week_report():
    today = date.today()
    week_start = today - timedelta(days=today.weekday())
    week_end = week_start + timedelta(days=7)
    return {
        "start_date": week_start.strftime("%Y-%m-%d"),
        "end_date": (week_end - timedelta(days=1)).strftime("%Y-%m-%d"),
        "days": get_daily_summary(week_start, week_end),
    }


def get_month_report(year=None, month=None):
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
        "days": get_daily_summary(start, end),
    }


def get_daily_summary(start_date, end_date):
    conn = get_connection()
    try:
        with conn.cursor() as cursor:
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
