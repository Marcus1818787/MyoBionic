import sys
sys.path.append('/home/myo/MyoBionic/src')
from Main import Hand
import time

entry = ''
hand = Hand()
while entry not in ['q','Q']:
    print("\nAvailable dev scripts:\n"
    "1. Test single servo\n"
    "2. Test all servos\n"
    "3. Display single Grip\n"
    "4. Cycle all Grips\n")
    entry = input("Enter a number between 1 & 4, enter q to quit: ")
    if entry == 'q':
        pass
    elif entry not in ['1','2','3','4']:
        print("Incorrect input, try again")
    elif entry == '1':
        finger_select = ''
        available_fingers = [str(i) for i in hand.finger_servo]
        while finger_select not in available_fingers:
            finger_select = input("Enter a number between 0 & 3: ")
            if finger_select not in available_fingers:
                print("Incorrect input, try again")
            else:
                hand.moveFinger(hand.finger_servo.get(int(finger_select)), 1)
                time.sleep(1)
                hand.moveFinger(hand.finger_servo.get(int(finger_select)), 0)
    elif entry == '2':
        hand.testServos()

    elif entry == '3':
        grip_select = ''
        available_grips = [str(i) for i in hand.grip_pattern]
        while grip_select not in available_grips:
            grip_select = input("Enter a number between 0 & 6: ")
            if grip_select not in available_grips:
                print("Incorrect input, try again")
            else:
                hand.changeGrip(int(grip_select))
    elif entry == '4':
        hand.cycleGrips()
