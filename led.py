import os
import time

# 공통 음극(common-cathode) LED  -> active_high=True
# 공통 양극(common-anode)  LED  -> active_high=False
# LED 색이 반전되거나 안 바뀌면 .env 에서 LED_ACTIVE_HIGH 값을 바꿔보세요.
LED_ACTIVE_HIGH = os.getenv("LED_ACTIVE_HIGH", "true").lower() == "true"
BRIGHTNESS = float(os.getenv("LED_BRIGHTNESS", 0.3))  # 밝기 0.0~1.0

# LED 핀(BCM). 기본 green=3/blue=2 는 I2C 핀이라 풀업 때문에 색이 안 꺼질 수 있음.
# 그럴 땐 풀업 없는 핀(예: 17/27/22)으로 배선하고 아래 env 만 바꾸면 됨.
LED_PIN_RED = int(os.getenv("LED_PIN_RED", 4))
LED_PIN_GREEN = int(os.getenv("LED_PIN_GREEN", 3))
LED_PIN_BLUE = int(os.getenv("LED_PIN_BLUE", 2))

try:
    from gpiozero import RGBLED
    _led = RGBLED(
        red=LED_PIN_RED, green=LED_PIN_GREEN, blue=LED_PIN_BLUE,
        active_high=LED_ACTIVE_HIGH,
    )
    _GPIO_AVAILABLE = True
except Exception as exc:
    # 에러를 삼키지 않고 출력 — LED 초기화 실패 시 원인이 보이게.
    print(f"[led] GPIO 초기화 실패, LED 비활성화: {exc!r}", flush=True)
    _led = None
    _GPIO_AVAILABLE = False

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


if __name__ == "__main__":
    # 단독 실행 진단: 순수 빨강 -> 초록 -> 파랑 순서로 표시.
    # 라벨과 실제 색이 다르면(예: "빨강"인데 청록색) 공통 양극 LED 이므로
    #   .env 에 LED_ACTIVE_HIGH=false 를 추가하세요.
    print(f"GPIO 사용가능: {_GPIO_AVAILABLE} | active_high={LED_ACTIVE_HIGH} | "
          f"pins R={LED_PIN_RED} G={LED_PIN_GREEN} B={LED_PIN_BLUE}")
    print("  먼저 전체 OFF (검정이어야 정상, 흰색이면 극성/풀업 문제)")
    clear_led()
    time.sleep(2)
    try:
        for name, rgb in (("빨강", (1, 0, 0)), ("초록", (0, 1, 0)), ("파랑", (0, 0, 1))):
            print(f"  {name} 표시 중...")
            _set_color(*rgb)
            time.sleep(2)
        print("측정 결과 색상: safe -> caution -> danger")
        for level in ("safe", "caution", "danger"):
            print(f"  {level}")
            show_result(level)
            time.sleep(2)
    finally:
        clear_led()
        if _GPIO_AVAILABLE:
            _led.close()
        print("종료")
