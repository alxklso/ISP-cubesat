import time
from Tasks.template_task import Task

"""
Every 10 minutes, this task turns on the Cosmic Watch for 1 minute, takes
measurements, and records data in a txt file on the SD card. The data will
be stored in a plain txt file. PyCubed interfaces with CW via payload bus pins.

The txt file name takes the format of <start_time>.txt
"""


class task(Task):
    priority = 10 # Set to low priority for now
    # TEST FREQ - 2 MINUTES, CHANGE TO 10 MINUTES AFTER VERIFICATION
    frequency = 1/120  
    name = 'cosmic watch'
    color = 'gray'

    # Set to True to skip first cycle of task
    schedule_later = False

    async def main_task(self):

        # Create start time using UNIX epoch time 
        # Used for file naming and to check when the task is finished
        startTime = str(time.time())

        with open("/sd/{}.txt".format(startTime), "w") as fp:
            # Continuously record data until 60 seconds later 
            while (time.time()-startTime) < 60:
                # Listen to uart2 pins 
                data = self.cubesat.uart2.read()

                if data:
                    # If buffer length is nonzero (there is data), decode
                    # and print to console
                    dataDecoded = data.decode("utf-8")
                    fp.write(dataDecoded)
                    print(dataDecoded)
            
            # When time is up, close the file.
            fp.close()
            print("File closed, now need to exit the task")

        # Debugging section
        self.debug("test start: {}".format(time.monotonic()))
        await self.cubesat.tasko.sleep(10)
        self.debug("test stop: {}".format(time.monotonic()))
