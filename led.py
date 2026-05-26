import time

import RPi.GPIO as GPIO


POWER = 19

# GPIO20 made the buzzer sound on this board, so keep it unused.
PINS = {
    "PIN16": 16,
    "PIN21": 21,
}


GPIO.setwarnings(False)
GPIO.setmode(GPIO.BCM)

GPIO.setup(POWER, GPIO.OUT)
GPIO.output(POWER, GPIO.HIGH)

for pin in PINS.values():
    GPIO.setup(pin, GPIO.OUT)


def all_off():
    for pin in PINS.values():
        GPIO.output(pin, GPIO.LOW)


try:
    all_off()

    for name, pin in PINS.items():
        print(f"{name} 테스트 시작")
        all_off()
        GPIO.output(pin, GPIO.HIGH)
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
