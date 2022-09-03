# Simplistic data recording
import multiprocessing
import sys
sys.path.append('../src/Libs')
import time
from pyomyo import Myo, emg_mode
import joblib
import numpy as np

MODE = emg_mode.PREPROCESSED
q = multiprocessing.Queue()
model = joblib.load('dev\MarcusSVM30.sav')


def worker(q):
	m = Myo(mode=MODE)
	m.connect()
	#print(f"Connected to Myo using {MODE}.")

	def add_to_queue(emg, movement):
		np_emg = np.asarray(emg).reshape(1, -1)
		grip = model.predict(np_emg)    # Classify EMG signals according to ML model
		q.put(str(grip))

	m.add_emg_handler(add_to_queue)
	start_time = time.time()
	data = []

	while True:
		while (time.time() - start_time < 2):
			m.run()
		while not q.empty():
			data.append(q.get())
		print(data)
		data.clear()
		time.sleep(2)
		start_time = time.time()


# -------- Main Program Loop -----------
if __name__ == '__main__':
	p = multiprocessing.Process(target=worker, args=(q,))
	try:
		p.start()
	except KeyboardInterrupt:
		p.terminate()
		p.join()
		print("Done")