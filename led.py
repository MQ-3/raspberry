import time

import RPi.GPIO as GPIO


# BCM GPIO numbers.
POWER = 19

# GPIO20 made a buzzer sound on this board, so do not drive it by default.
# Test the remaining candidate pins first.
TEST_PINS = {
    "PIN_16": 16,
    "PIN_21": 21,
}

# Keep this low while finding the correct RGB pins.
BRIGHTNESS = 2
PWM_FREQ = 1000


GPIO.setmode(GPIO.BCM)
GPIO.setup(POWER, GPIO.OUT)
GPIO.setup(list(TEST_PINS.values()), GPIO.OUT)

pwms = {
    name: GPIO.PWM(pin, PWM_FREQ)
    for name, pin in TEST_PINS.items()
}

for pwm in pwms.values():
    pwm.start(0)


def all_off():
    for pwm in pwms.values():
        pwm.ChangeDutyCycle(0)


def only_on(pin_name):
    for name, pwm in pwms.items():
        pwm.ChangeDutyCycle(BRIGHTNESS if name == pin_name else 0)


try:
    GPIO.output(POWER, GPIO.HIGH)

    while True:
        print("\n=== ACTIVE_HIGH LOW_BRIGHTNESS TEST ===")

        for pin_name, gpio_pin in TEST_PINS.items():
            all_off()
            only_on(pin_name)
            print(f"{pin_name} / GPIO{gpio_pin}")
            time.sleep(2)

        all_off()
        print("OFF")
        time.sleep(1)

except KeyboardInterrupt:
    all_off()
    for pwm in pwms.values():
        pwm.stop()
    GPIO.output(POWER, GPIO.LOW)
    GPIO.cleanup()
    print("종료")
