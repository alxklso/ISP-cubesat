from Tasks.template_task import Task
import time

"""
Every 10 minutes, this task turns on the Cosmic Watch for 1 minute, takes
measurements, and records data in the SD card. The data will be stored in a
plain txt file. PyCubed interfaces with CW via payload bus pins.

The text file name takes the format of <start_time>_<end_time>.txt
"""


class task(Task):
    priority = 1  # low priority, preempted by everything except LED
    # TEST FREQ - 2 MINUTES, CHANGE TO 10 MINUTES AFTER VERIFICATION
    frequency = 1/120  # once every 10 minutes, we listen to the UART pins
    name = 'cosmic watch'
    color = 'gray'

    # Set to True to skip first cycle of task
    schedule_later = False

    async def main_task(self):

        # Create custom file name that contains start and end timestamps
        # using UNIX time
        filename = "temp"

        with open("/sd/{}.txt".format(filename), "w") as fp:
            # Get time that the task starts at
            start = time.time()

            # Continuously record data until 60 seconds later 
            while (time.time()-start) < 60:
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
        self.debug('test start: {}'.format(time.monotonic()))
        await self.cubesat.tasko.sleep(10)
        self.debug('test stop: {}'.format(time.monotonic()))
