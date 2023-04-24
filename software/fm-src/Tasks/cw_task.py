import time, msgpack, adafruit_veml7700
from os import stat
from Tasks.template_task import Task

"""
FOR BENCHTOP TESTING: Every 2 minutes, this task turns on the Cosmic Watch
for 1 minute, takes measurements, and records data in a new plain txt file
on the SD card. PyCubed interfaces with CW via payload bus using I2C.

IN SPACE: Every 60 minutes, Cosmic Watch turns on for 1 minute, takes measurements, 
and records data into a new plain txt file with name and unix time stamp. The data
is saved in JSON format and uses the msgpack library.

Data measurement scheme:

    measurement = {
        "t" : unix epoch time,
        "s" : cw voltage meausurement
        "b" : battery pack voltage
    }
"""

class task(Task):
    priority = 10 
    # TEST FREQ = 1/120 
    # TODO: Change to FLIGHT FREQ = 1/(60*40)
    frequency = 1/120
    name = "cosmic watch"
    color = "gray"
    data_file = None
    sensor = None
    schedule_later = False

    # Initialize data file only once upon boot
    # So perform our task init and use that as a chance to init the data files
    def __init__(self, satellite):
        super().__init__(satellite)
        self.sensor = adafruit_veml7700.VEML7700(self.cubesat.i2c2)
        self.data_file = self.cubesat.new_file("/cw", binary = True)

    async def main_task(self):

        if self.data_file is not None:
            # Create start time using UNIX epoch time 
            # Used for file naming and to check when the task is finished
            # TODO: Change code from veml7700 to code from CW's ADC library 
            # https://github.com/adafruit/Adafruit_CircuitPython_ADS1x15
            print("Starting measurements")
            with open(self.data_file, "ab") as f:
                startTime = time.time()
                while (time.time() - startTime) < 60:
                    readings = {
                        "t": time.time(),
                        "s": self.sensor.light,
                        "b": self.cubesat.battery_voltage,
                    }
                    print(f"Measured {self.sensor.light} at time {time.time()}")
                    print(f"Battery pack voltage: {self.cubesat.battery_voltage}")
                    msgpack.pack(readings, f)
                    time.sleep(1)

            # Check if the file is getting bigger than we'd like
            if stat(self.data_file)[6] >= 256: # Bytes
                print("File reached 256 bytes... Sending")
                if self.cubesat.antenna_attached:
                    print(f"\nSend CW data file: {self.data_file}")
                    with open(self.data_file, "rb") as f:
                        chunk = f.read(32) # Each reading is 32 bytes when encoded
                        while chunk:
                            # We could send bigger chunks, radio packet can take 252 bytes
                            self.cubesat.radio1.send(f"KE8VDK{chunk}\0")
                            print(chunk)
                            chunk = f.read(32)
                    print("Finished\n")
                else:
                    # Print the unpacked data from the file
                    print(f"\nPrinting CW data file: {self.data_file}")
                    with open(self.data_file, "rb") as f:
                        while True:
                            try: print("\t", msgpack.unpack(f))
                            except: break
                    print("Finished\n")

                self.data_file = self.cubesat.new_file("/cw")