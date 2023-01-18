import time
import sys
sys.path.append('/home/myo/MyoBionic/src/Libs')
import joblib
import numpy as np

from pyomyo import Myo, emg_mode

if __name__ == '__main__':
    m = Myo(mode=emg_mode.PREPROCESSED)
    model = joblib.load('MarcusSVM30.sav')

    def pred_emg(emg, moving, times=[]):
        np_emg = np.asarray(emg).reshape(1, -1)
        grip = model.predict(np_emg)
        #print(grip)

        values.append(str(grip))

    m.add_emg_handler(pred_emg)
    m.connect()

    m.add_arm_handler(lambda arm, xdir: print('arm', arm, 'xdir', xdir))
    m.add_pose_handler(lambda p: print('pose', p))
    # m.add_imu_handler(lambda quat, acc, gyro: print('quaternion', quat))
    m.sleep_mode(1)
    m.set_leds([128, 128, 255], [128, 128, 255])  # purple logo and bar LEDs
    m.vibrate(1)

    values = []
    try:
        start_time = time.time()
        while True:
            m.run()
            if ((time.time() - start_time) > 2):
                start_time = time.time()
                #print(len(values))
                #values.clear()
                if (values.count(max(set(values), key=values.count)) > 90):
                    print(max(set(values), key=values.count))
                    values.clear()
    except KeyboardInterrupt:
        m.disconnect()
        quit()
