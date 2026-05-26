import RPi.GPIO as GPIO
import time

POWER = 19
RED = 16
GREEN = 20
BLUE = 21

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

    print("RED만 켭니다")
    all_off()
    GPIO.output(RED, GPIO.HIGH)
    time.sleep(5)

    print("GREEN만 켭니다")
    all_off()
    GPIO.output(GREEN, GPIO.HIGH)
    time.sleep(5)

    print("BLUE만 켭니다")
    all_off()
    GPIO.output(BLUE, GPIO.HIGH)
    time.sleep(5)

    print("모두 끕니다")
    all_off()
    GPIO.output(POWER, GPIO.LOW)

except KeyboardInterrupt:
    all_off()
    GPIO.output(POWER, GPIO.LOW)

finally:
    GPIO.cleanup()