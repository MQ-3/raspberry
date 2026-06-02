import time
import RPi.GPIO as GPIO

PIN_R = 4   # GCLK
PIN_G = 3   # SCL
PIN_B = 2   # SDA

GPIO.setwarnings(False)
GPIO.setmode(GPIO.BCM)
GPIO.setup([PIN_R, PIN_G, PIN_B], GPIO.OUT)


def all_off_high():
    GPIO.output([PIN_R, PIN_G, PIN_B], GPIO.HIGH)


def all_off_low():
    GPIO.output([PIN_R, PIN_G, PIN_B], GPIO.LOW)


try:
    print("=== 방식 1: 공통 캐소드 (HIGH = ON) ===")
    all_off_low()
    for name, pin in [("R(빨강)", PIN_R), ("G(초록)", PIN_G), ("B(파랑)", PIN_B)]:
        print(f"{name} 켜는 중...")
        GPIO.output(pin, GPIO.HIGH)
        time.sleep(2)
        GPIO.output(pin, GPIO.LOW)

    print("\n=== 방식 2: 공통 애노드 (LOW = ON) ===")
    all_off_high()
    for name, pin in [("R(빨강)", PIN_R), ("G(초록)", PIN_G), ("B(파랑)", PIN_B)]:
        print(f"{name} 켜는 중...")
        GPIO.output(pin, GPIO.LOW)
        time.sleep(2)
        GPIO.output(pin, GPIO.HIGH)

except KeyboardInterrupt:
    pass

finally:
    all_off_high()
    GPIO.cleanup()
    print("\n종료")
