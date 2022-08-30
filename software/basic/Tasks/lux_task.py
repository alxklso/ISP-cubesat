# Task to obtain lux sensor readings 

from Tasks.template_task import Task

class task(Task):
    priority = 7     # last priority for now 
    frequency = 1/60   # once every minute 
    name = 'lux_sensors'
    color = 'red'

    # Tell state machine to schedule the task for the first
    # time after one frequency period has passed. 
    schedule_later = True

    async def main_task(self):
        # Read in lux readings and store in dictionary
        lux_readings = {
            'lux1': self.cubesat.lux1,
            'lux2': self.cubesat.lux2,
            'lux3': self.cubesat.lux3,
            'lux4': self.cubesat.lux4,
        }

        # Store lux readings in cubesat data_cache object
        self.cubesat.data_cache.update({'lux_sensors': lux_readings})

        # Print the lux readings for debugging purposes w/ fancy formatting
        self.debug('Lux Readings:\n')
        for lux_type in self.cubesat.data_cache['lux_sensors']:
            #self.debug(lux_type[::]) # no fancy formatting 
            self.debug('{:>5} {}'.format(lux_type, self.cubesat.data_cache['lux_sensors'][lux_type]), 2) 