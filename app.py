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

        return success_response(get_week_report())
    except Exception as exc:
        return error_response(str(exc), 500)


@app.route("/api/calendar/month", methods=["GET"])
def calendar_month():
    try:
        from reports import get_month_report

        year = request.args.get("year", type=int)
        month = request.args.get("month", type=int)
        return success_response(get_month_report(year=year, month=month))
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


if __name__ == "__main__":
    app.run(host=config.FLASK_HOST, port=config.FLASK_PORT, debug=config.FLASK_DEBUG)
