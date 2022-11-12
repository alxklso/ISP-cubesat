from Tasks.template_task import Task
import time

"""
This task turns on the Cosmic Watch for a set amount of time, takes measurements,
and records data in the SD card. The data will be stored in a plain txt file.

To learn more about the Cosmic watch, visit go to https://http://www.cosmicwatch.lns.mit.edu/about
"""


class task(Task):
    priority = 10  # low priority, preempted by everything except LED
    frequency = 1 / 60  # once every 60 seconds
    name = 'cosmic watch'
    color = 'gray'

    """
    Setting schedule_later = True tells the state machine to skip the first iteration
    (1 unit of frequency defined above) of the task.
    schedule_later = True
    """
    schedule_later = True

    async def main_task(self):
        """
        For interacting with the Cosmic Watch's Arduino nano, we will be using a modified version of the
        Cosmic Watch script which initiates the Arduino code. Interfacing between the PyCubed and the Cosmic
        Watch is done through the payload terminals, using UART.
        """

        self.debug('test start: {}'.format(time.monotonic()))
        await self.cubesat.tasko.sleep(10)
        self.debug('test stop: {}'.format(time.monotonic()))
