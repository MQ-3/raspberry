import time
from gpiozero import RGBLED

BRIGHTNESS = 0.3  # 밝기 0.0~1.0

led = RGBLED(red=4, green=3, blue=2, active_high=True)


def set_color(r, g, b):
    led.color = (r / 255 * BRIGHTNESS, g / 255 * BRIGHTNESS, b / 255 * BRIGHTNESS)


try:
    print("빨강")
    set_color(255, 0, 0)
    time.sleep(2)

    print("초록")
    set_color(0, 255, 0)
    time.sleep(2)

    print("파랑")
    set_color(0, 0, 255)
    time.sleep(2)

    print("흰색")
    set_color(255, 255, 255)
    time.sleep(2)

    print("끔")
    led.off()

except KeyboardInterrupt:
    pass

finally:
    led.off()
    led.close()
    print("종료")
