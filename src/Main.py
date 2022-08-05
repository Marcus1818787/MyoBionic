from gpiozero import Servo
from time import sleep
import time

import joblib
import numpy as np
from pyomyo import Myo, emg_mode

thumb = Servo(21)
index = Servo(20)
middle = Servo(16)
ring_little = Servo(12)
servo_delay = 0.7

class Hand():
    def __init__(self):
        # Create a dictionary of servos for referencing, the current state of each servo
        # and the servo state for each grip
        self.finger_servo = {0:thumb, 1:index, 2:middle, 3:ring_little}
        self.current_state = {0:0, 1:0, 2:0, 3:0}
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

    def moveFinger(self, finger, open_close):
        # This opens the finger
        if open_close == 0:
            finger.max()
            sleep(servo_delay)
            finger.mid()
        else:
            finger.min()
            sleep(servo_delay)
            finger.mid()

    def changeGrip(self, grip):
        # Checks each servos current state against the state needed to achieve grip
        # If the state is different, the servo moves to the required state
        for i in range(4):
            if self.current_state[i] != self.grip_pattern[grip][i]:
                self.moveFinger(self.finger_servo[i], self.grip_pattern[grip][i])

