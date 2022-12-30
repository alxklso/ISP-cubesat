from Tasks.template_task import Task
import time

"""
Every 10 minutes, this task turns on the Cosmic Watch for 1 minute, takes
measurements, and records data in the SD card. The data will be stored in a
plain txt file.
"""


class task(Task):
    priority = 1  # low priority, preempted by everything except LED
    # TEST FREQ - 2 MINUTES, CHANGE TO 10 MINUTES AFTER VERIFICATION
    frequency = 1/120  # once every 10 minutes, we listen to the UART pins
    name = 'cosmic watch'
    color = 'gray'

    # State machine skips first iteration of the task
    schedule_later = False

    async def main_task(self):
        """
        For interacting with the Cosmic Watch's Arduino nano, we will be using
        a modified version of the Cosmic Watch script which initiates the Arduino
        code. Interfacing between the PyCubed and the Cosmic Watch is done through
        the payload bus, using UART.
        """

        # Debugging statements
        print("\nInside cosmicWatch.py")
        print("Recording data now\n")


        # Create the test.txt on the PyCubed SD card
        with open("/sd/cw_data.txt", "a") as fp:
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
