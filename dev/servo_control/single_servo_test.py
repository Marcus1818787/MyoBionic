import pigpio
import RPi.GPIO
import time

servo = 21
pi = pigpio.pi()

try:
    while True:
        pi.set_servo_pulsewidth(servo, 2000)
        time.sleep(0.5)
        pi.set_servo_pulsewidth(servo, 0)
        time.sleep(0.5)
        pi.set_servo_pulsewidth(servo, 1500)
        time.sleep(0.5)
except KeyboardInterrupt:
	print("Program stopped")