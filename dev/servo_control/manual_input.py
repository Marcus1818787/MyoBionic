def Manual_Entry(hand):
    entry = ''
    available_grips = [str(i) for i in hand.grip_pattern]
    while entry not in ['q','Q']:
        switch_state = GPIO.input(input_switch)
        if switch_state == 0:
            entry = input("Enter a number between 0 & 6, enter q to quit: ")
            if entry == 'q':
                pass
            elif entry not in available_grips:
                print("Incorrect input, try again")
            else:
                hand.changeGrip(int(entry))
        else:
            print("Switch is off, ignoring inputs for 2 seconds...")
            time.sleep(2)