from flask import Flask, render_template
from sensor import get_sensor_data
from state import classify, get_message

app = Flask(__name__)


@app.route("/")
def index():
    data = get_sensor_data()
    status = classify(data["avg"])
    message = get_message(status)

    return render_template(
        "index.html",
        raw_value=data["raw"],
        avg_value=data["avg"],
        status=status,
        message=message
    )


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
