import RPi.GPIO as GPIO
import time

POWER = 19   # BCM 19
RED   = 16   # BCM 16
GREEN = 20   # BCM 20
BLUE  = 21   # BCM 21

GPIO.setmode(GPIO.BCM)
GPIO.setup(POWER, GPIO.OUT)
GPIO.setup(RED, GPIO.OUT)
GPIO.setup(GREEN, GPIO.OUT)
GPIO.setup(BLUE, GPIO.OUT)

def all_off():
    GPIO.output(RED, GPIO.LOW)
    GPIO.output(GREEN, GPIO.LOW)
    GPIO.output(BLUE, GPIO.LOW)

try:
    GPIO.output(POWER, GPIO.HIGH)

    while True:
        # 빨강
        all_off()
        GPIO.output(RED, GPIO.HIGH)
        print("RED")
        time.sleep(1)

        # 초록
        all_off()
        GPIO.output(GREEN, GPIO.HIGH)
        print("GREEN")
        time.sleep(1)

        # 파랑
        all_off()
        GPIO.output(BLUE, GPIO.HIGH)
        print("BLUE")
        time.sleep(1)

        # 끄기
        all_off()
        print("OFF")
        time.sleep(1)

except KeyboardInterrupt:
    all_off()
    GPIO.output(POWER, GPIO.LOW)
    GPIO.cleanup()
    print("종료")