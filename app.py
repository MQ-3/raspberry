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

latest_result = None
_baseline = None
SPIKE_THRESHOLD = 20
_spi_lock = threading.Lock()


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
            with _spi_lock:
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

                # peak 확정 — 상태 판별 및 저장 (delta = peak - _baseline 기준)
                state = classify_sensor_value(peak, baseline=_baseline)
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
    with _spi_lock:
        reading = read_sensor()
    state = classify_sensor_value(reading.value, baseline=reading.baseline)
    print(
        f"[measure] baseline={reading.baseline} peak={reading.value} "
        f"delta={reading.value - reading.baseline:.0f} -> {state.level}",
        flush=True,
    )
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
        from reports import calc_heavy_drinking, calc_today_exceeded, save_drink_log

        data = request.get_json(silent=True) or {}
        required = ["sensor_value", "state_level", "state_label"]
        missing = [key for key in required if key not in data]
        if missing:
            return error_response(f"missing required fields: {', '.join(missing)}", 400)

        log_id = save_drink_log(data)
        user_id = data.get("user_id")
        exceeded = calc_today_exceeded(user_id)
        heavy = calc_heavy_drinking(user_id)
        return success_response({"message": "log saved", "id": log_id, "exceeded_tolerance": exceeded, "heavy_drinking": heavy}, 201)
    except Exception as exc:
        return error_response(str(exc), 500)


@app.route("/api/logs/today", methods=["GET"])
def logs_today():
    try:
        from reports import calc_heavy_drinking, calc_today_exceeded, get_today_logs

        user_id = request.args.get("user_id", type=int)
        exceeded = calc_today_exceeded(user_id)
        heavy = calc_heavy_drinking(user_id)
        return success_response({"logs": get_today_logs(user_id=user_id), "exceeded_tolerance": exceeded, "heavy_drinking": heavy})
    except Exception as exc:
        return error_response(str(exc), 500)


@app.route("/api/logs/range", methods=["GET"])
def logs_range():
    try:
        from datetime import datetime
        from reports import get_daily_summary

        start_str = request.args.get("start")
        end_str = request.args.get("end")
        user_id = request.args.get("user_id", type=int)

        if not start_str or not end_str:
            return error_response("start, end 파라미터가 필요합니다", 400)

        start = datetime.strptime(start_str, "%Y-%m-%d").date()
        end = datetime.strptime(end_str, "%Y-%m-%d").date()
        days = get_daily_summary(start, end, user_id=user_id)
        return success_response({"days": days})
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
        from reports import calc_heavy_drinking, save_drink_log
        from shorts import unlock_next_short_if_allowed

        data = request.get_json(silent=True) or {}
        user_id = data.get("user_id")

        # 과음 상태(주량 + 반병 초과)이면 측정 없이 차단
        if calc_heavy_drinking(user_id):
            return success_response(
                {
                    "unlocked": False,
                    "blocked": True,
                    "episode": None,
                    "message": "과음이 의심됩니다. 음주를 멈추세요.",
                }
            )

        reading, state = measure_once()
        save_drink_log(
            {
                "user_id": user_id,
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
                "blocked": False,
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


@app.route("/api/auth/profile", methods=["PUT"])
def auth_profile():
    try:
        from auth import update_profile

        data = request.get_json(silent=True) or {}
        if not data.get("user_id"):
            return error_response("user_id를 입력해주세요", 400)

        update_profile(
            data["user_id"],
            data.get("weight"),
            data.get("gender"),
            data.get("alcohol_tolerance"),
        )
        return success_response({"message": "프로필이 업데이트되었습니다"})
    except Exception as exc:
        return error_response(str(exc), 500)


@app.route("/api/auth/profile", methods=["GET"])
def auth_profile_get():
    try:
        from auth import get_profile

        user_id = request.args.get("user_id", type=int)
        if not user_id:
            return error_response("user_id를 입력해주세요", 400)

        user = get_profile(user_id)
        return success_response({"user": user})
    except ValueError as exc:
        return error_response(str(exc), 404)
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
    # 시작 시 LED 사용 가능 여부 표시 (False 면 모든 LED 호출이 무시됨)
    print(f"[app] LED GPIO 사용가능: {led._GPIO_AVAILABLE}", flush=True)

    # 시작 자가확인: 앱 프로세스가 LED 를 구동할 수 있는지 초록->빨강->끔 으로 확인
    print("[app] LED 자가확인: 초록 -> 빨강 -> 끔", flush=True)
    led.show_result("safe")
    time.sleep(0.8)
    led.show_result("danger")
    time.sleep(0.8)
    led.clear_led()

    # 백그라운드 센서 루프는 SPI를 측정과 동시에 점유해 값을 깨뜨리므로
    # 기본적으로 끔. /api/status 자동감지가 필요하면 ENABLE_SENSOR_LOOP=true.
    if config.ENABLE_SENSOR_LOOP:
        sensor_thread = threading.Thread(target=sensor_loop, daemon=True)
        sensor_thread.start()
    else:
        print("[app] sensor_loop 비활성화 (SPI 충돌 방지)", flush=True)

    app.run(host=config.FLASK_HOST, port=config.FLASK_PORT, debug=config.FLASK_DEBUG)
