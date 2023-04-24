import time
from Tasks.template_task import Task
import msgpack
from os import stat
import adafruit_veml7700

"""
FOR BENCHTOP TESTING: Every 2 minutes, this task turns on the Cosmic Watch
for 1 minute, takes measurements, and records data in a new plain txt file
on the SD card. PyCubed interfaces with CW via payload bus pins.

IN SPACE: Every 60 minutes, Cosmic Watch turns on for 1 minute, takes measurements, 
and records data into a new plain txt file with name and unix time stamp. The data
is saved in JSON format and uses the msgpack library.

Data measurement scheme:

    measurement = {
        "time" : unix epoch time,
        "voltage" : cw voltage meausurement
    }
"""

SEND_DATA = False

class task(Task):
    priority = 10 # Set to low priority for now
    # TEST FREQ = 2 MINUTES (FREQ = 1/120)
    # FLIGHT FREQ = 10 MINUTES (FREQ = 1/600)
    frequency = 1/120
    name = "cosmic watch"
    color = "gray"
    data_file = None
    sensor = None

    # Set to True to skip first cycle of task
    schedule_later = False

    # We want to initialize the data file only once upon boot
    # So perform our task init and use that as a chance to init the data files
    def __init__(self, satellite):
        super().__init__(satellite)
        self.sensor = adafruit_veml7700.VEML7700(self.cubesat.i2c2)
        self.data_file = self.cubesat.new_file("/sd/cw", binary = True)

    async def main_task(self):

        if self.data_file is not None:
            # Create start time using UNIX epoch time 
            # Used for file naming and to check when the task is finished
            print("Starting measurements")
            with open(self.data_file, "ab") as f:
                startTime = time.time()
                while (time.time() - startTime) < 60:
                    readings = {
                        "time": time.time(),
                        "voltage": self.sensor.light
                    }
                    print(f"Measured {self.sensor.light} at time {time.time()}")
                    msgpack.pack(readings, f)
                    time.sleep(0.5)

            # Check if the file is getting bigger than we'd like
            if stat(self.data_file)[6] >= 256: # Bytes
                print("File reached 256 bytes... Sending")
                if SEND_DATA:
                    print(f"\nSend CW data file: {self.data_file}")
                    with open(self.data_file, "rb") as f:
                        chunk = f.read(64) # Each reading is 64 bytes when encoded
                        while chunk:
                            # We could send bigger chunks, radio packet can take 252 bytes
                            self.cubesat.radio1.send(f"[KE8VDK]{chunk}[KE8VDK]\0")
                            print(chunk)
                            chunk = f.read(64)
                    print("Finished\n")
                else:
                    # Print the unpacked data from the file
                    print(f"\nPrinting CW data file: {self.data_file}")
                    with open(self.data_file, "rb") as f:
                        while True:
                            try: print("\t", msgpack.unpack(f))
                            except: break
                    print("Finished\n")

                self.data_file = self.cubesat.new_file("/sd/cw")