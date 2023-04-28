import time
from Tasks.template_task import Task

"""
This task checks the battery voltage against a voltage threshold 
to check for low batteries. 
"""

class task(Task):
    priority = 1
    frequency = 1/(60*60*24) # once every day
    testing_frequency = 1/(2*60) # once every 5 mins
    name = "vbatt"
    color = "red"
    timeout = 60*60 # 60 min
    schedule_later = True

    async def main_task(self):
        # If all other fault-handling fails, hard reset the PyCubed
        self.debug("Resetting to clamp monotonic drift")
        time.sleep(10)
        self.cubesat.micro.on_next_reset(self.cubesat.micro.RunMode.NORMAL)
        self.cubesat.micro.reset()