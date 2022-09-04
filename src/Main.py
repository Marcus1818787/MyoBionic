try:
    import RPi.GPIO as GPIO
except ModuleNotFoundError:
    from GPIOEmulator.EmulatorGUI import GPIO
#from gpiozero import Servo
import pigpio
import Adafruit_GPIO.SPI as SPI
import Adafruit_MCP3008
from pyomyo import Myo, emg_mode

import time
import joblib
import numpy
import multiprocessing

pi = pigpio.pi()

# Initiate variables for servo control
thumb = 21
index = 20
middle = 16
ring_little = 12
servo_delay = 0.7
threshold = 300

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

# Initiate ML variables
myo_q = multiprocessing.Queue()
myo_data = []
model = joblib.load('TrainedModels\MarcusSVM30.sav')    # Change this file path to change the ML model usedemg_sample_time = 2


class Hand():
    def __init__(self):
        # finger_servo indexes each servo to a number
        self.finger_servo = {0:thumb, 1:index, 2:middle, 3:ring_little}
        # current_state indexes whether each servo is relaxed(0) or contracted(1)
        self.current_state = {0:0, 1:0, 2:0, 3:0}
        # grip_pattern indexes the state of each servo (ascending order) required to achieve grip patterns
        self.grip_pattern = {0:[1,1,1,1], 1:[0,1,1,1], 2:[1,0,1,1],
                             3:[1,0,0,1], 4:[1,1,0,0], 5:[1,0,0,0], 6:[0,0,0,0]}

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
            # This timer will be used to ignore rush current values that interfere with voltmeter
            rush_current_timer = time.time()
            while limit_reach == False:
                # Split the dictionary into a list of keys & values, find the index of the value,
                #   then reference the key with the same index. This relies on the pinout being correct (servo1-4 = channel0-3)
                resistor_channel = list(self.finger_servo.keys())[list(self.finger_servo.values()).index(finger)]
                resistor_value = mcp.read_adc(resistor_channel)
                print(resistor_value)
                if (resistor_value > threshold) and ((time.time()-rush_current_timer) > 0.5):  # The servo is straining against something, it should stop
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
        for i in range(3,-1,-1):
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
    connected = multiprocessing.Value('i', 0)
    p = multiprocessing.Process(target=EMG_collector, args=(myo_q, connected,))
    p.start()
    start_time = time.time()

    while True:
        if (connected.value == 1) and (time.time() - start_time > 2):
            while not(myo_q.empty()):
                emg = list(myo_q.get()) # Empty the queue into myo_data list
                myo_data.append(emg[0])
            if (len(myo_data) != 0) and (myo_data.count(max(set(myo_data), key=myo_data.count)) > 90): # If the same grip has been recognised more than 90 times in 2 seconds
                new_grip = (max(set(myo_data), key=myo_data.count))   # Set the most common grip as the new grip
                print(new_grip)
                hand.changeGrip(new_grip,)   # Move the servos to replicate the new grip
            myo_data.clear()  # Clear the list to start collecting grip values again
            start_time = time.time()


def EMG_collector(myo_q, connected):
    m = Myo(mode=emg_mode.PREPROCESSED)
    m.connect()
	
    def add_to_queue(emg, movement):
        np_emg = numpy.asarray(emg).reshape(1, -1)
        grip = model.predict(np_emg)    # Classify EMG signals according to ML model
        myo_q.put(grip)        # Add this classification to the list to calculate mode later

    m.add_emg_handler(add_to_queue)

	 # Orange logo and bar LEDs
    m.set_leds([128, 0, 0], [128, 0, 0])
	# Vibrate to know we connected okay
    m.vibrate(1)
    connected.value = 1
    print("connected")
	
    # worker function
    while True:
	    m.run()
    print("Worker Stopped")


# Main Program
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
    