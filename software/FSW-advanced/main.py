import os
import time
import lib.tasko as tasko
import traceback
from lib.pycubed import cubesat


"""
FSW Main written by the ISP Software Team. Creates a queue of tasks from Tasks 
folder and runs them according to task class attributes (priority, frequency). 
Includes fault-handling and hard reset for PyCubed if needed.

"""


############# HELPER FUNCTIONS START ############# 

def showScheduledTasks():
    # Show all tasks scheduled to run and task count
    print("\nTasks scheduled to run (count: {})".format(len(cubesat.scheduled_tasks)))
    print("-"*50)
    for task_key, task_value in cubesat.scheduled_tasks.items():
        print(task_key + " -- " + str(task_value))

def hardReset():
    # If all other fault-handling fails, hard reset the PyCubed
    print('Engaging fail-safe: hard reset')
    time.sleep(10)
    cubesat.micro.on_next_reset(cubesat.micro.RunMode.NORMAL)
    cubesat.micro.reset()

############# HELPER FUNCTIONS END ############# 



############# MAIN PORTION START ############# 

print('Initializing PyCubed...')
# Create asyncio object
cubesat.tasko=tasko
# Dict to store scheduled objects by name
cubesat.scheduled_tasks={}

# Schedule all tasks in Tasks directory
print('Loading Tasks...', end='')
for file in os.listdir('Tasks'):
    # Remove py extension from file name
    file = file[:-3]

    # ignore these files
    if file in ("template_task","test_task","listen_task") or file.startswith('._'):
        continue

    # Import the task's file
    exec('import Tasks.{}'.format(file))
    # Create helper object for scheduling the task
    task_obj = eval('Tasks.'+file).task(cubesat)

    # Determine value of task's schedule_later variable 
    # If true, skip first cycle of task
    if hasattr(task_obj, 'schedule_later') and getattr(task_obj, 'schedule_later'):
        schedule = cubesat.tasko.schedule_later
    else:
        schedule = cubesat.tasko.schedule

    # Schedule each task object
    cubesat.scheduled_tasks[task_obj.name]=schedule(task_obj.frequency, task_obj.main_task, task_obj.priority)

# Show all scheduled tasks
showScheduledTasks()

# Driver code, runs forever
print('\nRunning...')
try:
    # Run forever
    cubesat.tasko.run()
except Exception as e:
    formatted_exception = traceback.format_exception(e, e, e.__traceback__)
    print(formatted_exception)
    try:
        # Increment NVM error counter
        cubesat.c_state_err+=1
        # Try logging everything
        cubesat.log('{},{},{}'.format(formatted_exception, cubesat.c_state_err, cubesat.c_boot))
    except:
        pass


# If all fault-handling fails, hard reset PyCubed
hardReset()
