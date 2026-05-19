import time


def show_idle():
    print("[LED] idle mode")


def show_measure_progress():
    print("[LED] measure progress start")
    for step in range(1, 11):
        print(f"[LED] gauge {step * 10}%")
        time.sleep(0.03)
    print("[LED] measure progress end")


def show_result(state_level):
    colors = {
        "safe": "green",
        "caution": "yellow/orange",
        "danger": "red",
    }
    print(f"[LED] result: {state_level} -> {colors.get(state_level, 'off')}")


def clear_led():
    print("[LED] clear")
