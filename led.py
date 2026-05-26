import RPi.GPIO as GPIO
import time

POWER = 19
PINS = {
    "PIN16": 16,
    "PIN20": 20,
    "PIN21": 21,
}

GPIO.setwarnings(False)
GPIO.setmode(GPIO.BCM)

GPIO.setup(POWER, GPIO.OUT)
GPIO.output(POWER, GPIO.HIGH)

for pin in PINS.values():
    GPIO.setup(pin, GPIO.OUT)

def all_off():
    # active-low 가정: HIGH가 OFF
    for pin in PINS.values():
        GPIO.output(pin, GPIO.HIGH)

try:
    all_off()

    for name, pin in PINS.items():
        print(f"{name} 테스트 시작")
        all_off()
        GPIO.output(pin, GPIO.LOW)   # 하나만 켜기
        time.sleep(3)

    print("모두 끔")
    all_off()
    time.sleep(1)

except KeyboardInterrupt:
    pass

finally:
    all_off()
    GPIO.output(POWER, GPIO.LOW)
    GPIO.cleanup()
    print("종료")