import time
import led

print("측정 중 연출")
led.show_measure_progress()
time.sleep(3)

print("안전")
led.show_result("safe")
time.sleep(2)

print("주의")
led.show_result("caution")
time.sleep(2)

print("위험")
led.show_result("danger")
time.sleep(2)

led.clear_led()
print("끔")
