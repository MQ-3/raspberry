import RPi.GPIO as GPIO
import time

POWER = 19   # BCM 19
RED   = 16   # BCM 16
GREEN = 20   # BCM 20
BLUE  = 21   # BCM 21

# If GREEN makes a buzzer sound, this pin is probably shared with or wired to a buzzer.
# Lower duty reduces the noise while you verify the real J31 green pin mapping.
GREEN_DUTY = 8
PWM_FREQ = 1000

GPIO.setmode(GPIO.BCM)
GPIO.setup(POWER, GPIO.OUT)
GPIO.setup(RED, GPIO.OUT)
GPIO.setup(GREEN, GPIO.OUT)
GPIO.setup(BLUE, GPIO.OUT)
green_pwm = GPIO.PWM(GREEN, PWM_FREQ)
green_pwm.start(0)

def all_off():
    GPIO.output(RED, GPIO.LOW)
    green_pwm.ChangeDutyCycle(0)
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
        green_pwm.ChangeDutyCycle(GREEN_DUTY)
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
    green_pwm.stop()
    GPIO.output(POWER, GPIO.LOW)
    GPIO.cleanup()
    print("종료")
