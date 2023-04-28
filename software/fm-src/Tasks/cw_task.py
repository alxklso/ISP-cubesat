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
        "t" : unix epoch time,
        "vlt" : cw voltage meausurement
        "val" : cw value measurement
    }
"""

class task(Task):
    priority = 10 
    frequency = 1/(60*40)
    testing_frequency = 1/120
    name = "cosmic watch"
    color = "gray"
    data_file = None
    sensor = None
    schedule_later = False

    cw_path = "/cw"

    # Initialize data file only once upon boot
    # So perform our task init and use that as a chance to init the data files
    def __init__(self, satellite):
        super().__init__(satellite)
        self.ads= ADS.ADS1115(self.cubesat.i2c2)
        self.chan = AnalogIn(self.ads, ADS.P0)
        self.check_and_delete_files()
        self.data_file = self.cubesat.new_file(self.cw_path, binary = True)

    async def main_task(self):
        self.check_and_delete_files()
        if self.data_file is not None:
            # Create start time using UNIX epoch time 
            # Used for file naming and to check when the task is finished
            # TODO: Change code from veml7700 to code from CW's ADC library 
            # https://github.com/adafruit/Adafruit_CircuitPython_ADS1x15
            print("Starting measurements")
            
            with open(self.data_file, "ab") as f:
                startTime = time.time()
                while (time.time() - startTime) < (60*3):
                    #time with corresponding voltage
                    readings = {
                        "t": supervisor.ticks_ms(),
                        "vlt": self.chan.voltage,
                        "val": self.chan.value
                    }
                    #prints measured voltage of AnalogIn channel connected to ADS1115 at current time
                    print(f"Measured {readings['vlt']}v and value {readings['val']} at time {time.time()}")
                    msgpack.pack(readings, f)
                    time.sleep(1)

            # Check if the file is getting bigger than we'd like
            if stat(self.data_file)[6] >= 245: # Bytes
                with open(self.data_file, "rb") as f:
                    while True:
                        try: print("\t", msgpack.unpack(f))
                        except: break

                self.data_file = self.cubesat.new_file(self.cw_path)

    def get_sorted_files(self, directory):
        try:
            files = [f for f in os.listdir(directory) if os.path.isfile(os.path.join(directory, f))]
            files.sort()
            return files
        except:
            return []
    
    def delete_extra_files(self, file_list, deletion_dir):
        # We only store up to 512 files 
        try:
            while len(file_list) >= 512:
                file_to_delete = file_list.pop(0)
                os.remove(os.path.join(deletion_dir, file_to_delete))
        except:
            pass
        return file_list
    
    def delete_file(self, files, directory):
        try:
            file_to_delete = files.pop(0)
            os.remove(os.path.join(directory, file_to_delete))
            dir_size -= os.path.getsize(os.path.join(directory, file_to_delete))
        except:
            pass
        return files

    def check_and_delete_files(self):
        cw_dir = f"/sd/{self.cw_path}"
        cw_read_dir = f"/sd/{self.cw_path}_read"

        # Sort files, oldest to newest
        read_files = self.get_sorted_files(cw_read_dir)
        files = self.get_sorted_files(cw_dir)

        # Make sure each dir doesn't have too many files
        read_files = self.delete_extra_files(read_files, cw_read_dir)
        files = self.delete_extra_files(files, cw_dir)
        
        # File deletion logic
        # How much space is remaining:
        fs_stats = os.statvfs('/sd')
        available_space = fs_stats.f_bavail * fs_stats.f_frsize
        print(f"Remaining space is {available_space}")
        
        # If less than 1 MB of space remaining, delete the files one by one until there is enough space left
        if available_space <= 1000000:
            print("Deleting files from SD card...")
            #delete files until we have enough space
            while available_space < 1000000:
                if len(read_files) == 0 and len(read_files) == 0:
                    break
                
                if len(read_files) > 0:
                    read_files = self.delete_file(read_files, cw_read_dir)
                if len(files) > 0:
                    files = self.delete_file(files, cw_dir)