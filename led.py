import time

import RPi.GPIO as GPIO


# The document values are wiringPi numbers:
# RED 27 -> BCM 16
# GREEN 28 -> BCM 20
# BLUE 29 -> BCM 21
RED = 16
GREEN = 20
BLUE = 21

# Set this to None when the RGB module's common pin is connected to 3.3V/5V/GND.
# GPIO19 may be a separate J31 power-control pin on some boards, but it can also
# make diagnosis harder, so this test does not drive it by default.
POWER = None

BRIGHTNESS = 2
PWM_FREQ = 1000

PINS = {
    "RED": RED,
    "GREEN": GREEN,
    "BLUE": BLUE,
}


GPIO.setmode(GPIO.BCM)
if POWER is not None:
    GPIO.setup(POWER, GPIO.OUT)
    GPIO.output(POWER, GPIO.HIGH)

GPIO.setup(list(PINS.values()), GPIO.OUT)

pwms = {name: GPIO.PWM(pin, PWM_FREQ) for name, pin in PINS.items()}
for pwm in pwms.values():
    pwm.start(0)


def set_active_high(color_name=None):
    for name, pwm in pwms.items():
        pwm.ChangeDutyCycle(BRIGHTNESS if name == color_name else 0)


def set_active_low(color_name=None):
    for name, pwm in pwms.items():
        pwm.ChangeDutyCycle(100 - BRIGHTNESS if name == color_name else 100)


def all_off():
    set_active_high(None)


def run_active_high_test():
    print("\n=== ACTIVE_HIGH TEST ===")
    for name, pin in PINS.items():
        set_active_high(name)
        print(f"{name} / BCM{pin}")
        time.sleep(2)
    set_active_high(None)
    print("OFF")
    time.sleep(1)


def run_active_low_test():
    print("\n=== ACTIVE_LOW TEST ===")
    for name, pin in PINS.items():
        set_active_low(name)
        print(f"{name} / BCM{pin}")
        time.sleep(2)
    set_active_low(None)
    print("OFF")
    time.sleep(1)


try:
    while True:
        run_active_high_test()
        run_active_low_test()

except KeyboardInterrupt:
    all_off()
    for pwm in pwms.values():
        pwm.stop()
    if POWER is not None:
        GPIO.output(POWER, GPIO.LOW)
    GPIO.cleanup()
    print("종료")
