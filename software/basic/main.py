import os
import lib.tasko as tasko
from lib.pycubed import cubesat

"""
PyCubed Beep-Sat FSW
M. Holliday
Modified by: Alex Kelso (Systems Lead @ Isomer Space Program)
"""

print('\n{lines}\n{:^40}\n{lines}\n'.format('Beep-Sat Demo', lines='-' * 40))
print('Initializing PyCubed Hardware...')

# Create asyncio object
cubesat.tasko = tasko
# Dict to store scheduled objects by name
cubesat.scheduled_tasks = {}

print('Loading Tasks...\n')

# Iterate through all tasks in directory
# Return type of os.listdir is a list of file names
for file in os.listdir('Tasks'): 
    # Remove the '.py' extension from file name
    file = file[:-3]

    # Ignore these files
    if file in ("template_task", "test_task", "listen_task") or file.startswith('._'):
        continue

    # Import statement for each task file is built and executed using built-in exec() function
    exec('import Tasks.{}'.format(file))
    # Create a helper object for scheduling the task
    task_obj = eval('Tasks.' + file).task(cubesat)

    # Determine if the task wishes to be scheduled later
    # If schedule_later = True, then the task is delayed for one unit of frequency, as 
    # defined in the task file.
    if hasattr(task_obj, 'schedule_later') and getattr(task_obj, 'schedule_later'):
        schedule = cubesat.tasko.schedule_later
    else:
        schedule = cubesat.tasko.schedule

    # Schedule each task object and add it to our dict
    cubesat.scheduled_tasks[task_obj.name] = schedule(task_obj.frequency, task_obj.main_task, task_obj.priority)
print("Total tasks scheduled:", len(cubesat.scheduled_tasks))

print('Running...')
# runs forever
cubesat.tasko.run()
