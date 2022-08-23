try:
    import RPi.GPIO as GPIO
except ModuleNotFoundError:
    from GPIOEmulator.EmulatorGUI import GPIO
#from gpiozero import Servo
from multiprocessing import current_process
import pigpio
import Adafruit_GPIO.SPI as SPI
import Adafruit_MCP3008
import time

import joblib
import numpy as np
from pyomyo import Myo, emg_mode

pi = pigpio.pi()

# Initiate variables for servo control
thumb = 21
index = 20
middle = 16
ring_little = 12
servo_delay = 0.7
threshold = 200

# Initiate variables for the ADC
CLK = 4
MISO = 17
MOSI = 27
CS = 22
mcp = Adafruit_MCP3008.MCP3008(clk=CLK, cs=CS, miso=MISO, mosi=MOSI)

input_switch = 18
GPIO.setmode(GPIO.BCM)
GPIO.setwarnings(False)
GPIO.setup(input_switch, GPIO.IN)


class Hand():
    def __init__(self):
        # finger_servo indexes each servo to a number (0-3)
        self.finger_servo = {0:thumb, 1:index, 2:middle, 3:ring_little}
        # current_state indexes whether each servo is relaxed(0) or contracted(1)
        self.current_state = {0:0, 1:0, 2:0, 3:0}
        # grip_pattern indexes the state of each servo (thumb - little) required to achieve patterns 0 - 6
        self.grip_pattern = {0:[1,1,1,1], 1:[0,1,1,1], 2:[1,0,1,1],
                             3:[1,0,0,1], 4:[1,1,0,0], 5:[1,0,0,0], 6:[0,0,0,0]}

        # Attempt to establish if any of the servos are contracted based off values the last time the hand was on
        boot_contract = open("current_state.txt", 'r')
        for finger in self.current_state:
            servo_status = boot_contract.readline()
            # Set current state of finger to the state declared in txt file
            self.current_state[finger] = int(servo_status)
            # If the servo is contracted, relax it
            if self.current_state[finger] == 1:
                self.moveFinger(self.finger_servo[finger], 0)


    def moveFinger(self, finger, open_close): # if open_close=1, that signals to close the finger, 0 signals to open it
        limit_reach = False
        start_time = time.time()
        # This closes the finger
        if open_close == 1:
            while limit_reach == False:
                # Split the dictionary into a list of keys & values, find the index of the value,
                #   then reference the key with the same index. This relies on the pinout being correct (servo1-4 = channel0-3)
                resistor_channel = list(self.finger_servo.keys())[list(self.finger_servo.values()).index(finger)]
                resistor_value = mcp.read_adc(resistor_channel)
                if (resistor_value > threshold) and ((time.time() - start_time) > 2):  # The servo is straining against something, it should stop
                    pi.set_servo_pulsewidth(finger, 0)
                    time.sleep(servo_delay)
                    pi.set_servo_pulsewidth(finger, 1500)   # Set servo to default position
                    time.sleep(1)
                    limit_reach = True
                    pi.set_servo_pulsewidth(finger, 0)
                else:
                    pi.set_servo_pulsewidth(finger, 2000)   # Servo has not met resistance, keep going
        else:
            pi.set_servo_pulsewidth(finger, 1000)   # Uniwnds the servo by one full rotation
            time.sleep(1)
            pi.set_servo_pulsewidth(finger, 0)
            pi.set_servo_pulsewidth(finger, 1500)   # Set servo to default position
            time.sleep(1)
            

    def testServos(self):
        # This for loop will contract, pause, then relax each finger
        for finger in self.finger_servo:
            self.moveFinger(self.finger_servo.get(finger), 1)
            time.sleep(2)
            self.moveFinger(self.finger_servo.get(finger), 0)


    def changeGrip(self, grip):
        # Checks each servos current state against the state needed to achieve grip
        # If the state is different, the servo moves to the required state
        for i in range(4):
            if self.current_state[i] != self.grip_pattern[grip][i]:
                self.moveFinger(self.finger_servo[i], self.grip_pattern[grip][i])
                self.current_state[i] = self.grip_pattern[grip][i]


def Manual_Entry(hand):
    entry = ''
    available_grips = [str(i) for i in hand.grip_pattern]
    while entry not in ['q','Q']:
        entry = input("Enter a number between 0 & 6, enter q to quit: ")
        if entry == 'q':
            pass
        elif entry not in available_grips:
            print("Incorrect input, try again")
        else:
            hand.changeGrip(int(entry))

if __name__ == '__main__':
    hand = Hand()
    hand.testServos()
    
