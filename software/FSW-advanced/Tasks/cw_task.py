import time
from Tasks.template_task import Task
import msgpack
from os import stat

"""
Every 10 minutes, this task turns on the Cosmic Watch for 1 minute, takes
measurements, and records data in a new plain txt file on the SD card.
PyCubed interfaces with CW via payload bus pins.

The txt file name takes the format of <start_time>.txt
"""

SEND_DATA = False

class task(Task):
    priority = 10 # Set to low priority for now
    # TEST FREQ - 2 MINUTES, CHANGE TO 10 MINUTES AFTER VERIFICATION
    frequency = 1/120  
    name = 'cosmic watch'
    color = 'gray'
    data_file = None

    # Set to True to skip first cycle of task
    schedule_later = False

    # we want to initialize the data file only once upon boot
    # so perform our task init and use that as a chance to init the data files
    def __init__(self,satellite):
        super().__init__(satellite)
        self.data_file=self.cubesat.new_file('/sd/cw',binary=True)

    async def main_task(self):

        if self.data_file is not None:
            # Create start time using UNIX epoch time 
            # Used for file naming and to check when the task is finished
            with open(self.data_file,'ab') as f:
                startTime = str(time.time())
                while (time.time()-startTime) < 60:
                    data = self.cubesat.uart2.read()
                    dataDecoded = data.decode("utf-8")
                    # fill in code here based on format of decoded string
                    msgpack.pack(dataDecoded,f)

            # check if the file is getting bigger than we'd like
            if stat(self.data_file)[6] >= 256: # bytes
                if SEND_DATA:
                    print('\nSend CW data file: {}'.format(self.data_file))
                    with open(self.data_file,'rb') as f:
                        chunk = f.read(64) # each reading is 64 bytes when encoded
                        while chunk:
                            # we could send bigger chunks, radio packet can take 252 bytes
                            self.cubesat.radio1.send(chunk)
                            print(chunk)
                            chunk = f.read(64)
                    print('finished\n')
                else:
                    # print the unpacked data from the file
                    print('\nPrinting CW data file: {}'.format(self.data_file))
                    with open(self.data_file,'rb') as f:
                        while True:
                            try: print('\t',msgpack.unpack(f))
                            except: break
                    print('finished\n')
            
            self.data_file=self.cubesat.new_file('/sd/cw')

        # Debugging section
        self.debug("test start: {}".format(time.monotonic()))
        await self.cubesat.tasko.sleep(10)
        self.debug("test stop: {}".format(time.monotonic()))
