# Simplistic data recording
import sys
sys.path.append('../src/Libs')
import time
from pyomyo import Myo, emg_mode
import joblib
import numpy as np


def data_worker(mode, seconds):
	collect = True

	print("Data Worker started to collect")
	# Start collecing data.
	start_time = time.time()

	while collect:
		if (time.time() - start_time < seconds):
			m.run()
		else:
			collect = False
			collection_time = time.time() - start_time
			print("Finished collecting.")
			print(f"Collection time: {collection_time}")
			print(len(myo_data), "frames collected")

			# Add columns and save to df
			print(myo_data)
			myo_data.clear()

# -------- Main Program Loop -----------
if __name__ == '__main__':

	def add_to_queue(emg, movement):
		np_emg = np.asarray(emg).reshape(1, -1)
		grip = model.predict(np_emg)    # Classify EMG signals according to ML model
		myo_data.append(str(grip))        # Add this classification to the list to calculate mode later
	
	seconds = 2
	myo_data = []
	mode = emg_mode.PREPROCESSED
	model = joblib.load('src\TrainedModels\MarcusSVM30.sav')

	# ------------ Myo Setup ---------------
	m = Myo(mode=mode)
	m.connect()
	m.add_emg_handler(add_to_queue)

	 # Its go time
	m.set_leds([0, 128, 0], [0, 128, 0])
	# Vibrate to know we connected okay
	m.vibrate(1)

	while True:
		data_worker(mode, seconds)
		print("next read done")
		time.sleep(3)
