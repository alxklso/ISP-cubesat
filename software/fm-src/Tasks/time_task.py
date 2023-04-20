# Print the time in seconds since boot every 20 seconds
from Tasks.template_task import Task
import time

class task(Task):
    priority = 4
    frequency = 1/20 # Once every 20 seconds
    name = "time"
    color = "white"

    async def main_task(self):
        t_since_boot = time.monotonic() - self.cubesat.BOOTTIME
        self.debug(f"{t_since_boot}s since boot")