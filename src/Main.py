try:
    import RPi.GPIO as GPIO
except ModuleNotFoundError:
    from GPIOEmulator.EmulatorGUI import GPIO
#from gpiozero import Servo
import pigpio
import Adafruit_GPIO.SPI as SPI
import Adafruit_MCP3008
from Libs.pyomyo import Myo, emg_mode

import time
import joblib
import numpy as np
from multiprocessing import Process

pi = pigpio.pi()

# Initiate variables for servo control
thumb = 21
index = 20
middle = 16
ring_little = 12
servo_delay = 0.7
threshold = 350

# Initiate variables for the ADC
CLK = 4
MISO = 17
MOSI = 27
CS = 22
mcp = Adafruit_MCP3008.MCP3008(clk=CLK, cs=CS, miso=MISO, mosi=MOSI)

# Initiate variables for input switch
input_switch = 18
GPIO.setmode(GPIO.BCM)
GPIO.setwarnings(False)
GPIO.setup(input_switch, GPIO.IN)


class Hand():
    def __init__(self):
        # finger_servo indexes each servo to a number
        self.finger_servo = {0:ring_little, 1:middle, 2:index, 3:thumb}
        # current_state indexes whether each servo is relaxed(0) or contracted(1)
        self.current_state = {0:0, 1:0, 2:0, 3:0}
        # grip_pattern indexes the state of each servo (ascending order) required to achieve grip patterns
        self.grip_pattern = {0:[1,1,1,1], 1:[1,1,1,0], 2:[1,1,0,1],
                             3:[1,0,0,1], 4:[0,0,1,1], 5:[0,0,0,1], 6:[0,0,0,0]}

        # Attempt to establish if any of the servos are contracted based off values the last time the hand was on
        boot_state = open("current_state.txt", 'r')
        for finger in self.current_state:
            servo_status = boot_state.readline()
            # Set current state of finger to the state declared in txt file
            self.current_state[finger] = int(servo_status)
            # If the servo is contracted, relax it
            if self.current_state[finger] == 1:
                self.moveFinger(self.finger_servo[finger], 0)
        boot_state.close()


    def moveFinger(self, finger, open_close): # if open_close=1, that signals to close the finger, 0 signals to open it
        limit_reach = False

        if open_close == 1:
            while limit_reach == False:
                # Split the dictionary into a list of keys & values, find the index of the value,
                #   then reference the key with the same index. This relies on the pinout being correct (servo1-4 = channel0-3)
                resistor_channel = list(self.finger_servo.keys())[list(self.finger_servo.values()).index(finger)]
                resistor_value = mcp.read_adc(resistor_channel)
                print(resistor_value)
                if (resistor_value > threshold):  # The servo is straining against something, it should stop
                    pi.set_servo_pulsewidth(finger, 0)
                    time.sleep(servo_delay)
                    pi.set_servo_pulsewidth(finger, 1500)   # Set servo to default position
                    time.sleep(servo_delay)
                    pi.set_servo_pulsewidth(finger, 0)
                    limit_reach = True
                else:
                    pi.set_servo_pulsewidth(finger, 2000)   # Servo has not met resistance, keep going
        else:
            pi.set_servo_pulsewidth(finger, 1000)   # Uniwnds the servo by one full rotation
            time.sleep(servo_delay)
            pi.set_servo_pulsewidth(finger, 1500)   # Set servo to default position
            time.sleep(servo_delay)
            pi.set_servo_pulsewidth(finger, 0)
            
    def changeGrip(self, grip):
        # Checks each servos current state against the state needed to achieve grip
        # If the state is different, the servo moves to the required state
        for i in range(4):
            if self.current_state[i] != self.grip_pattern[grip][i]:
                self.moveFinger(self.finger_servo[i], self.grip_pattern[grip][i])
                self.current_state[i] = self.grip_pattern[grip][i]
                # This is where the servo state should be chnaged in the boot_state

    def testServos(self):
        # This for loop will contract, pause, then relax each finger
        for finger in self.finger_servo:
            self.moveFinger(self.finger_servo.get(finger), 1)
            time.sleep(1)
            self.moveFinger(self.finger_servo.get(finger), 0)

    def cycleGrips(self):
        for grip in self.grip_pattern:
            self.changeGrip(grip)
            time.sleep(4)


def Manual_Entry(hand):
    entry = ''
    available_grips = [str(i) for i in hand.grip_pattern]
    while entry not in ['q','Q']:
        switch_state = GPIO.input(input_switch)
        if switch_state == 1:
            entry = input("Enter a number between 0 & 6, enter q to quit: ")
            if entry == 'q':
                pass
            elif entry not in available_grips:
                print("Incorrect input, try again")
            else:
                hand.changeGrip(int(entry))
                hand.stopHand()
        else:
            print("Switch is off, ignoring inputs for 2 seconds...")
            time.sleep(2)


def EMG_Entry(hand):
    m = Myo(mode=emg_mode.PREPROCESSED)
    model = joblib.load('TrainedModels/MarcusSVM30.sav')    # Change this file path to change the ML model used

    def pred_emg(emg, moving, times=[]):
        np_emg = np.asarray(emg).reshape(1, -1)
        grip = model.predict(np_emg)    # Classify EMG signals according to ML model
        values.append(str(grip))        # Add this classification to the list to calculate mode later

    m.add_emg_handler(pred_emg)
    m.connect()

    m.add_arm_handler(lambda arm, xdir: print('arm', arm, 'xdir', xdir))
    m.add_pose_handler(lambda p: print('pose', p))
    m.sleep_mode(1)
    m.set_leds([128, 128, 255], [128, 128, 255])  # purple logo and bar LEDs
    m.vibrate(1)

    values = [] # This list will store classified EMG signals to register grip held by user
    start_time = time.time()
    proc = Process(target=m.run)
    #proc.start()
    while True:
        #m.run()
        proc.start()
        if ((time.time() - start_time) > 2):
            print("two seconds lapped")
            if (values.count(max(set(values), key=values.count)) > 90): # If the same grip has been recognised more than 90 times in 2 seconds
                #m.disconnect()
                proc.terminate()
                proc.join()
                new_grip = int(max(set(values), key=values.count)[1])   # Set the most common grip as the new grip
                hand.changeGrip(new_grip,)   # Move the servos to replicate the new grip
                print("grip changed")
                values.clear()  # Clear the list to start collecting grip values again
                print("values cleared")
                proc.start()
                #m.connect()
            start_time = time.time()    # Reset 2 second counter
            print("timer reset")

if __name__ == '__main__':
    hand = Hand()
    program_run = True
    while program_run:
        print("Enter the number of the routine you want to run:\n1. Manual keyboard input\n"
        "2. EMG input\n3. Test servos\n4. Cycle grip examples\n5. Exit program")
        mode = input("Enter an input option: ")
        if (mode in ['1', 'Manual', 'manual', 'keyboard', 'Keyboard']):
            Manual_Entry(hand)
        elif (mode in ['2', 'EMG', 'emg']):
            EMG_Entry(hand)
        elif (mode in ['3', 'Test', 'test', 'Test servos', 'test servos']):
            hand.testServos()
        elif (mode in ['4', 'Cycle', 'cycle', 'Cycle grips', 'Cycle grip examples']):
            hand.cycleGrips()
        elif (mode in ['5', 'Exit', 'exit']):
            program_run = False
        else:
            print("Incorrect input, please enter the number associated with your choice.")
    