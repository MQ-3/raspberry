import time

try:
    from gpiozero import RGBLED
    _led = RGBLED(red=4, green=3, blue=2, active_high=True)
    _GPIO_AVAILABLE = True
except Exception:
    _led = None
    _GPIO_AVAILABLE = False

BRIGHTNESS = 0.3  # 밝기 0.0~1.0

_COLORS = {
    "safe":    (0,   1,   0),    # 초록
    "caution": (1,   0.5, 0),    # 주황
    "danger":  (1,   0,   0),    # 빨강
}


def _set_color(r, g, b):
    if not _GPIO_AVAILABLE:
        return
    _led.color = (r * BRIGHTNESS, g * BRIGHTNESS, b * BRIGHTNESS)


def show_measure_progress():
    """측정 중 노란색 3회 깜빡임 후 유지."""
    for _ in range(3):
        _set_color(1, 1, 0)
        time.sleep(0.2)
        _set_color(0, 0, 0)
        time.sleep(0.2)
    _set_color(1, 1, 0)


def show_result(level: str):
    """측정 완료 후 상태별 색상 표시."""
    r, g, b = _COLORS.get(level, (0, 0, 0))
    _set_color(r, g, b)


def clear_led():
    """LED 끄기."""
    if not _GPIO_AVAILABLE:
        return
    _led.off()
