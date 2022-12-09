from Tasks.template_task import Task
import time

"""
This task turns on the Cosmic Watch for a set amount of time, takes measurements,
and records data in the SD card. The data will be stored in a plain txt file.

To learn more about the Cosmic watch, visit go to https://http://www.cosmicwatch.lns.mit.edu/about
"""


class task(Task):
    priority = 10  # low priority, preempted by everything except LED
    frequency = 1 / 600  # once every 10 minutes, we listen to the UART pins
    name = 'cosmic watch'
    color = 'gray'

    # State machine skips first iteration of the task
    schedule_later = True

    async def main_task(self):
        """
        For interacting with the Cosmic Watch's Arduino nano, we will be using a modified version of the
        Cosmic Watch script which initiates the Arduino code. Interfacing between the PyCubed and the Cosmic
        Watch is done through the payload terminals, using UART.
        """
        # Listen to uart2 pins 
        data = self.cubesat.uart2.read()

        
        if data:
            # If buffer length is nonzero (there is data), decode
            # and print to console
            dataDecoded = data.decode("utf-8")
            fp.write(dataDecoded)

        # Debugging section
        self.debug('test start: {}'.format(time.monotonic()))
        await self.cubesat.tasko.sleep(10)
        self.debug('test stop: {}'.format(time.monotonic()))
