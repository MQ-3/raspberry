import time

import RPi.GPIO as GPIO


# BCM GPIO numbers.
POWER = 19
RED = 16
GREEN = 20
BLUE = 21

# Lower this if the LED is still too bright.
BRIGHTNESS = 3
PWM_FREQ = 1000

COLOR_PINS = {
    "RED": RED,
    "GREEN": GREEN,
    "BLUE": BLUE,
}


GPIO.setmode(GPIO.BCM)
GPIO.setup(POWER, GPIO.OUT)
GPIO.setup(list(COLOR_PINS.values()), GPIO.OUT)

pwms = {
    name: GPIO.PWM(pin, PWM_FREQ)
    for name, pin in COLOR_PINS.items()
}

for pwm in pwms.values():
    pwm.start(0)


def duty_for(active_low, on):
    if active_low:
        return 100 - BRIGHTNESS if on else 100
    return BRIGHTNESS if on else 0


def all_off(active_low):
    for pwm in pwms.values():
        pwm.ChangeDutyCycle(duty_for(active_low, False))


def only_on(color_name, active_low):
    for name, pwm in pwms.items():
        pwm.ChangeDutyCycle(duty_for(active_low, name == color_name))


def run_test(active_low):
    mode = "COMMON_ANODE / ACTIVE_LOW" if active_low else "COMMON_CATHODE / ACTIVE_HIGH"
    print(f"\n=== {mode} ===")
    all_off(active_low)
    time.sleep(1)

    for color_name in COLOR_PINS:
        only_on(color_name, active_low)
        print(color_name)
        time.sleep(2)

    all_off(active_low)
    print("OFF")
    time.sleep(1)


try:
    GPIO.output(POWER, GPIO.HIGH)

    while True:
        run_test(active_low=False)
        run_test(active_low=True)

except KeyboardInterrupt:
    for pwm in pwms.values():
        pwm.stop()
    GPIO.output(POWER, GPIO.LOW)
    GPIO.cleanup()
    print("종료")
