# Simplistic data recording
import sys
sys.path.append('/home/myo/MyoBionic/src/Libs')
import time
import multiprocessing
import pandas as pd
from Libs.pyomyo import Myo, emg_mode


def data_worker(mode, seconds, filepath):
	collect = True

	# ------------ Myo Setup ---------------
	m = Myo(mode=mode)
	m.connect()

	myo_data = []

	def add_to_queue(emg, movement):
		myo_data.append(emg)

	m.add_emg_handler(add_to_queue)

	def print_battery(bat):
		print("Battery level:", bat)

	m.add_battery_handler(print_battery)

	 # Its go time
	m.set_leds([0, 128, 0], [0, 128, 0])
	# Vibrate to know we connected okay
	m.vibrate(1)

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
			myo_cols = ["Channel_1", "Channel_2", "Channel_3", "Channel_4", "Channel_5", "Channel_6", "Channel_7", "Channel_8"]
			myo_df = pd.DataFrame(myo_data, columns=myo_cols)
			myo_df.to_csv(filepath, index=False)
			print("CSV Saved at: ", filepath)

# -------- Main Program Loop -----------
if __name__ == '__main__':
	seconds = 3
	# Uncomment & change any of the following 8 lines individually to save to the required file.
	# Do not uncomment more than one line, else file name will be overwritten with the last uncommented line
	#file_name = "EMGData/0/0-40/Fist40.csv"
	#file_name = "EMGData/1/1-40/Thumb40.csv"
	#file_name = "EMGData/2/2-40/Index40.csv"
	#file_name = "EMGData/3/3-40/Two40.csv"
	#file_name = "EMGData/4/4-30/Three30.csv"
	#file_name = "EMGData/5/5-40/Four40.csv"
	#file_name = "EMGData/6/6-40/Palm40.csv"
	mode = emg_mode.PREPROCESSED
	p = multiprocessing.Process(target=data_worker, args=(mode, seconds, file_name))
	p.start()
