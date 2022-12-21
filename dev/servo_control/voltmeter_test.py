import pigpio
import RPi.GPIO
import time
import Adafruit_MCP3008


servo = 21
CLK = 21
MISO = 20
MOSI = 16
CS = 12
mcp = Adafruit_MCP3008.MCP3008(clk=CLK, cs=CS, miso=MISO, mosi=MOSI)

pi = pigpio.pi()
threshold = 300
servo_delay = 0.5

try:
    while True:
        # This timer will be used to ignore rush current values that interfere with voltmeter
            rush_current_timer = time.time()
            while limit_reach == False:
                # Split the dictionary into a list of keys & values, find the index of the value,
                #   then reference the key with the same index. This relies on the pinout being correct (servo1-4 = channel0-3)
                resistor_channel = 0
                resistor_value = mcp.read_adc(resistor_channel)
                if (resistor_value > threshold) and ((time.time()-rush_current_timer) > 2):  # The servo is straining against something, it should stop
                    pi.set_servo_pulsewidth(servo, 0)
                    time.sleep(servo_delay)
                    pi.set_servo_pulsewidth(servo, 1500)   # Set servo to default position
                    time.sleep(servo_delay)
                    pi.set_servo_pulsewidth(servo, 0)
                    limit_reach = True
                else:
                    pi.set_servo_pulsewidth(servo, 2000)   # Servo has not met resistance, keep going
except KeyboardInterrupt:
	print("Program stopped")