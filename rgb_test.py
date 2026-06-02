import time
import RPi.GPIO as GPIO

PIN_R = 4  # GCLK
PIN_G = 3  # SCL
PIN_B = 2  # SDA

GPIO.setwarnings(False)
GPIO.setmode(GPIO.BCM)
GPIO.setup([PIN_R, PIN_G, PIN_B], GPIO.OUT)

pwm_r = GPIO.PWM(PIN_R, 100)
pwm_g = GPIO.PWM(PIN_G, 100)
pwm_b = GPIO.PWM(PIN_B, 100)

pwm_r.start(0)
pwm_g.start(0)
pwm_b.start(0)


def set_color(r, g, b):
    pwm_r.ChangeDutyCycle(r / 255 * BRIGHTNESS)
    pwm_g.ChangeDutyCycle(g / 255 * BRIGHTNESS)
    pwm_b.ChangeDutyCycle(b / 255 * BRIGHTNESS)


BRIGHTNESS = 30  # 밝기 0~100

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
    set_color(0, 0, 0)

except KeyboardInterrupt:
    pass

finally:
    set_color(0, 0, 0)
    pwm_r.stop()
    pwm_g.stop()
    pwm_b.stop()
    GPIO.output([PIN_R, PIN_G, PIN_B], GPIO.LOW)
    GPIO.cleanup()
    print("종료")
