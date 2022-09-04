import multiprocessing
import time
import joblib
import numpy
import multiprocessing

from pyomyo import Myo, emg_mode

# ------------ Myo Setup ---------------
myo_q = multiprocessing.Queue()
myo_data = []
model = joblib.load('MarcusSVM30.sav')    # Change this file path to change the ML model used


def worker(myo_q, connected):
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
	
	"""worker function"""
	while True:
		m.run()
	print("Worker Stopped")

# -------- Main Program Loop -----------
if __name__ == "__main__":
	connected = multiprocessing.Value('i', 0)
	p = multiprocessing.Process(target=worker, args=(myo_q, connected,))
	p.start()
	start_time = time.time()

	while True:
		if (connected.value == 1) and (time.time() - start_time > 2):
			while not(myo_q.empty()):
				emg = list(myo_q.get())
				myo_data.append(emg[0])
			if (len(myo_data) != 0) and (myo_data.count(max(set(myo_data), key=myo_data.count)) > 90): # If the same grip has been recognised more than 90 times in 2 seconds
				new_grip = (max(set(myo_data), key=myo_data.count))   # Set the most common grip as the new grip
				print(new_grip)
			myo_data.clear()  # Clear the list to start collecting grip values again
			start_time = time.time()
