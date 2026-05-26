import RPi.GPIO as GPIO
import time

LIGHTCONTROL = 5   # 먼저 5로 테스트

GPIO.setmode(GPIO.BCM)
GPIO.setup(LIGHTCONTROL, GPIO.OUT)

try:
    while True:
        GPIO.output(LIGHTCONTROL, GPIO.HIGH)
        print("LED BAR ON")
        time.sleep(1)

        GPIO.output(LIGHTCONTROL, GPIO.LOW)
        print("LED BAR OFF")
        time.sleep(1)

except KeyboardInterrupt:
    GPIO.output(LIGHTCONTROL, GPIO.LOW)
    GPIO.cleanup()
    print("종료")