from lib.pycubed import cubesat 
import msgpack
import time
from os import stat
import adafruit_veml7700

data_file = None
SEND_DATA = False # Do not turn to true until antenna is connected
data_file=cubesat.new_file('/data/cw',binary=True)
sensor = adafruit_veml7700.VEML7700(cubesat.i2c2)

while True:
    if data_file is not None:
        # Create start time using UNIX epoch time 
        # Used for file naming and to check when the task is finished
        print("Starting measurements")
        with open(data_file,'ab') as f:
            startTime = time.time()
            while (time.time() - startTime) < 3:
                readings = {
                    'time': time.time(),
                    'voltage': sensor.light
                }
                print("Measured {} at time {}".format(sensor.light, time.time()))
                msgpack.pack(readings, f)
                time.sleep(0.5)

        # check if the file is getting bigger than we'd like
        if stat(data_file)[6] >= 256: # bytes
            print("File reached 256 bytes... Sending")
            if SEND_DATA:
                print('\nSend CW data file: {}'.format(data_file))
                with open(data_file,'rb') as f:
                    chunk = f.read(64) # each reading is 64 bytes when encoded
                    while chunk:
                        # we could send bigger chunks, radio packet can take 252 bytes
                        cubesat.radio1.send(chunk)
                        print(chunk)
                        chunk = f.read(64)
                print('finished\n')
            else:
                # print the unpacked data from the file
                print('\nPrinting CW data file: {}'.format(data_file))
                with open(data_file,'rb') as f:
                    while True:
                        try: print('\t', msgpack.unpack(f))
                        except: break
                print('finished\n')