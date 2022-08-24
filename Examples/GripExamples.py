from Main import Hand
from time import sleep

example_hand = Hand()
# Simply cycle through each of the available grip patterns
for grip in example_hand.grip_pattern:
    example_hand.changeGrip(example_hand.grip_pattern[grip])
    sleep(5)