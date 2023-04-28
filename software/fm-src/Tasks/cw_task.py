import time, msgpack
from os import stat
import os
from Tasks.template_task import Task
import adafruit_ads1x15.ads1115 as ADS #ADC import
from adafruit_ads1x15.analog_in import AnalogIn #ADC collects data from voltage src at pin 0
import supervisor

"""
FOR BENCHTOP TESTING: Every 2 minutes, this task turns on the Cosmic Watch
for 1 minute, takes measurements, and records data in a new plain txt file
on the SD card. PyCubed interfaces with CW via payload bus using I2C.

IN SPACE: Every 60 minutes, Cosmic Watch turns on for 1 minute, takes measurements, 
and records data into a new plain txt file with name and unix time stamp. The data
is saved in JSON format and uses the msgpack library.

Data measurement scheme:

    measurement = {
        "t" : time in ms,
        "vlt" : cw voltage meausurement,
        "val" : cw value measurement
    }
"""

class task(Task):
    priority = 4
    frequency = 1/(60*60) # Once an hour
    testing_frequency = 1/20
    name = "cosmic watch"
    color = "gray"
    sensor = None
    schedule_later = False

    # Initialize data file only once upon boot
    # So perform our task init and use that as a chance to init the data files
    def __init__(self, satellite):
        super().__init__(satellite)
        self.ads= ADS.ADS1115(self.cubesat.i2c2)
        self.chan = AnalogIn(self.ads, ADS.P0)

    async def main_task(self):
        self.check_and_delete_files()
        data_file = self.cubesat.new_file("/cw/cw", binary = True)

        if data_file is not None:
            self.debug("Starting measurements")
            
            with open(data_file, "ab") as f:
                startTime = time.time()
                recording_time = 60*3
                if self.cubesat.benchtop_testing:
                    recording_time = 10
                while (time.time() - startTime) < recording_time:
                    #time with corresponding voltage
                    readings = {
                        "t": supervisor.ticks_ms(),
                        "vlt": self.chan.voltage,
                        "val": self.chan.value
                    }
                    #prints measured voltage of AnalogIn channel connected to ADS1115 at current time
                    self.debug(f"Measured {readings['vlt']}v and value {readings['val']} at time {time.time()}")
                    msgpack.pack(readings, f)
                    time.sleep(1)

            # Check if the file is getting bigger than we'd like
            if stat(data_file)[6] >= 128: # Bytes
                with open(data_file, "rb") as f:
                    while True:
                        try: print("\t", msgpack.unpack(f))
                        except: break

    def get_sorted_files(self, directory):
        files = []
        try:
            if self.cubesat.hardware["SDcard"]:
                files = [f"{directory}/{f}" for f in os.listdir(directory)]
                files.sort()
        except:
            self.debug("Could not get sorted files")
        return files
    
    def delete_extra_files(self, file_list):
        
        self.debug(f"We have {len(file_list)} files")
        try:
            if self.cubesat.hardware["SDcard"]:
                while len(file_list) > 0:
                    file_to_delete = file_list.pop(0)
                    self.debug(f"Deleting: {file_to_delete}")
                    os.remove(file_to_delete)
        except:
            self.debug("Could not delete extra files")
        return file_list

    def check_and_delete_files(self):
        cw_dir = f"/sd/cw"

        # Sort files, oldest to newest
        files = self.get_sorted_files(cw_dir)

        self.debug("Checking files to see if we have too many")
        # Make sure each dir doesn't have too many files
        files = self.delete_extra_files(files)