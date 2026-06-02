import time

try:
    import RPi.GPIO as GPIO
    _GPIO_AVAILABLE = True
except ImportError:
    _GPIO_AVAILABLE = False

POWER_PIN = 19
RED_PIN = 16
GREEN_PIN = 21

# active-low: LOW = on, HIGH = off
_LEVEL_PINS = {
    "safe":    (False, True),   # red off, green on
    "caution": (True,  True),   # red on,  green on  → yellow
    "danger":  (True,  False),  # red on,  green off
}


def _setup():
    if not _GPIO_AVAILABLE:
        return
    GPIO.setwarnings(False)
    GPIO.setmode(GPIO.BCM)
    GPIO.setup(POWER_PIN, GPIO.OUT)
    GPIO.output(POWER_PIN, GPIO.HIGH)
    GPIO.setup(RED_PIN, GPIO.OUT)
    GPIO.setup(GREEN_PIN, GPIO.OUT)
    _all_off()


def _all_off():
    if not _GPIO_AVAILABLE:
        return
    GPIO.output(RED_PIN, GPIO.HIGH)
    GPIO.output(GREEN_PIN, GPIO.HIGH)


def _set_leds(red: bool, green: bool):
    if not _GPIO_AVAILABLE:
        return
    GPIO.output(RED_PIN, GPIO.LOW if red else GPIO.HIGH)
    GPIO.output(GREEN_PIN, GPIO.LOW if green else GPIO.HIGH)


_setup()


def show_measure_progress():
    """측정 중임을 나타내는 게이지 연출 (3회 깜빡임 후 점등 유지)."""
    for _ in range(3):
        _set_leds(True, True)
        time.sleep(0.2)
        _all_off()
        time.sleep(0.2)
    _set_leds(True, True)


def show_result(level: str):
    """측정 완료 후 상태별 색상 표시."""
    red, green = _LEVEL_PINS.get(level, (False, False))
    _set_leds(red, green)


def clear_led():
    """LED 끄기."""
    _all_off()
