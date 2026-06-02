import threading  # 새로 추가: 백그라운드 센서 루프용
import time  # 새로 추가: 루프 대기시간용 (대기시간 값은 백엔드 담당자와 논의 필요)
from datetime import datetime  # 새로 추가: spike 감지 시각 기록용

from flask import Flask, jsonify, request

try:
    from flask_cors import CORS
except ImportError:
    def CORS(app):
        @app.after_request
        def add_cors_headers(response):
            response.headers["Access-Control-Allow-Origin"] = "*"
            response.headers["Access-Control-Allow-Headers"] = "Content-Type"
            response.headers["Access-Control-Allow-Methods"] = "GET, POST, OPTIONS"
            return response

        return app

import config
import led
from sensor import read_sensor
from state import classify_sensor_value, state_to_dict

app = Flask(__name__)
CORS(app)

# 새로 추가: 가장 최근 spike 결과를 담는 전역변수
latest_result = None

# 새로 추가: baseline 추적 전역변수
_baseline = None

# 새로 추가: baseline 대비 이 값 이상 오르면 숨 분 것으로 판단
SPIKE_THRESHOLD = 20


# 새로 추가: 백그라운드 센서 루프 (상시 측정 + spike 감지)
def sensor_loop():
    global latest_result, _baseline

    try:
        from adc import MCP3208
        adc = MCP3208()
    except Exception:
        return

    try:
        while True:
            value = adc.read_channel(config.SENSOR_CHANNEL)

            if _baseline is None:
                _baseline = value
                time.sleep(config.SENSOR_LOOP_INTERVAL)
                continue

            if value - _baseline >= SPIKE_THRESHOLD:
                # spike 감지 — 값이 내려올 때까지 peak 추적
                peak = value
                while True:
                    time.sleep(config.SENSOR_LOOP_INTERVAL)
                    value = adc.read_channel(config.SENSOR_CHANNEL)
                    if value > peak:
                        peak = value
                    elif value < _baseline + SPIKE_THRESHOLD:
                        break

                # peak 확정 — 상태 판별 및 저장
                state = classify_sensor_value(peak)
                now = datetime.now()

                latest_result = {
                    "breath_detected": True,
                    "sensor_value": peak,
                    "state_level": state.level,
                    "state_label": state.label,
                    "detected_at": now.strftime("%Y-%m-%d %H:%M:%S"),
                }

                # B 방식: DB 저장은 프론트가 user_id 붙여서 /api/logs로 요청
                _baseline = None

            else:
                # spike 아닐 때 baseline 서서히 갱신
                _baseline = _baseline * 0.9 + value * 0.1

            time.sleep(config.SENSOR_LOOP_INTERVAL)

    finally:
        adc.close()


def success_response(data=None, status_code=200):
    payload = {"success": True}
    if data:
        payload.update(data)
    return jsonify(payload), status_code


def error_response(message, status_code=500):
    return jsonify({"success": False, "message": message}), status_code


def measure_once():
    led.show_measure_progress()
    reading = read_sensor()
    state = classify_sensor_value(reading.value)
    led.show_result(state.level)
    return reading, state


@app.route("/api/health", methods=["GET"])
def health():
    return success_response({"message": "server is running"})


@app.route("/api/db/init", methods=["POST"])
def init_db():
    try:
        from db import init_tables

        init_tables()
        return success_response({"message": "database tables are ready"})
    except Exception as exc:
        return error_response(str(exc), 500)


@app.route("/api/measure", methods=["POST"])
def measure():
    try:
        reading, state = measure_once()
        return success_response(
            {
                "sensor_value": reading.value,
                "source": reading.source,
                "samples": reading.samples,
                "average": round(reading.average, 1),
                "state": state_to_dict(state),
            }
        )
    except Exception as exc:
        led.clear_led()
        return error_response(str(exc), 500)


@app.route("/api/logs", methods=["POST"])
def create_log():
    try:
        from reports import save_drink_log

        data = request.get_json(silent=True) or {}
        required = ["sensor_value", "state_level", "state_label"]
        missing = [key for key in required if key not in data]
        if missing:
            return error_response(f"missing required fields: {', '.join(missing)}", 400)

        log_id = save_drink_log(data)
        return success_response({"message": "log saved", "id": log_id}, 201)
    except Exception as exc:
        return error_response(str(exc), 500)


@app.route("/api/logs/today", methods=["GET"])
def logs_today():
    try:
        from reports import get_today_logs

        return success_response({"logs": get_today_logs()})
    except Exception as exc:
        return error_response(str(exc), 500)


@app.route("/api/logs/week", methods=["GET"])
def logs_week():
    try:
        from reports import get_week_report

        user_id = request.args.get("user_id", type=int)  # 새로 추가: user_id 파라미터
        return success_response(get_week_report(user_id=user_id))
    except Exception as exc:
        return error_response(str(exc), 500)


@app.route("/api/calendar/month", methods=["GET"])
def calendar_month():
    try:
        from reports import get_month_report

        year = request.args.get("year", type=int)
        month = request.args.get("month", type=int)
        user_id = request.args.get("user_id", type=int)  # 새로 추가: user_id 파라미터
        return success_response(get_month_report(year=year, month=month, user_id=user_id))
    except Exception as exc:
        return error_response(str(exc), 500)


@app.route("/api/shorts", methods=["GET"])
def shorts_list():
    try:
        from shorts import get_shorts

        return success_response({"shorts": get_shorts()})
    except Exception as exc:
        return error_response(str(exc), 500)


@app.route("/api/shorts/unlock", methods=["POST"])
def shorts_unlock():
    try:
        from reports import save_drink_log
        from shorts import unlock_next_short_if_allowed

        reading, state = measure_once()
        save_drink_log(
            {
                "sensor_value": reading.value,
                "state_level": state.level,
                "state_label": state.label,
                "state_message": state.message,
                "memo": "AI 숏츠 체크인",
            }
        )
        unlock_result = unlock_next_short_if_allowed(state.level)

        return success_response(
            {
                "sensor_value": reading.value,
                "state": state_to_dict(state),
                "unlocked": unlock_result["unlocked"],
                "episode": unlock_result["episode"],
                "message": unlock_result["message"],
            }
        )
    except Exception as exc:
        led.clear_led()
        return error_response(str(exc), 500)


@app.route("/api/auth/register", methods=["POST"])
def auth_register():
    try:
        from auth import register_user

        data = request.get_json(silent=True) or {}
        if not data.get("email") or not data.get("password"):
            return error_response("email과 password를 입력해주세요", 400)

        user = register_user(data["email"], data["password"])
        return success_response({"user": user}, 201)
    except ValueError as exc:
        return error_response(str(exc), 409)
    except Exception as exc:
        return error_response(str(exc), 500)


@app.route("/api/auth/login", methods=["POST"])
def auth_login():
    try:
        from auth import login_user

        data = request.get_json(silent=True) or {}
        if not data.get("email") or not data.get("password"):
            return error_response("email과 password를 입력해주세요", 400)

        user = login_user(data["email"], data["password"])
        return success_response({"user": user})
    except ValueError as exc:
        return error_response(str(exc), 401)
    except Exception as exc:
        return error_response(str(exc), 500)


@app.route("/api/auth/delete", methods=["DELETE"])
def auth_delete():
    try:
        from auth import delete_user

        data = request.get_json(silent=True) or {}
        if not data.get("user_id"):
            return error_response("user_id를 입력해주세요", 400)

        delete_user(data["user_id"])
        return success_response({"message": "계정이 삭제되었습니다"})
    except ValueError as exc:
        return error_response(str(exc), 404)
    except Exception as exc:
        return error_response(str(exc), 500)


@app.route("/api/status", methods=["GET"])
def status():
    if latest_result is None:
        return success_response({"breath_detected": False})
    return success_response(latest_result)


if __name__ == "__main__":
    # 새로 추가: 백그라운드 센서 루프 스레드 시작
    sensor_thread = threading.Thread(target=sensor_loop, daemon=True)
    sensor_thread.start()

    app.run(host=config.FLASK_HOST, port=config.FLASK_PORT, debug=config.FLASK_DEBUG)
