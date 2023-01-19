import os, time, traceback
import lib.tasko as tasko
from lib.pycubed import cubesat


"""
FSW MAIN: Creates a queue of tasks from Tasks folder and runs them
according to task class attributes (priority, frequency). Includes
fault-handling and hard reset for PyCubed if needed.
"""


############# HELPER FUNCTIONS START ############# 

def showScheduledTasks():
    """
    Shows all tasks scheduled to run and the task count. 
    Remove in flight source.
    """

    print("\nTasks scheduled to run (count: {})".format(len(cubesat.scheduled_tasks)))
    print("-"*50)
    for task_key, task_value in cubesat.scheduled_tasks.items():
        print(task_key + " -- " + str(task_value))


def hardReset():
    """
    If all other fault-handling fails, hard reset the PyCubed board.
    """

    # If all other fault-handling fails, hard reset the PyCubed
    print('Engaging fail-safe: hard reset')
    time.sleep(10)
    cubesat.micro.on_next_reset(cubesat.micro.RunMode.NORMAL)
    cubesat.micro.reset()


def startupRoutine():
    """
    Startup routine after pod deployment which is only supposed to 
    happen once. The following tasks are executed (in order):
        - Trigger burn wire
        - Set burn wire bit flag
        - TODO: Send test beacons and listen for ground confirmation
        - 5 sec. buffer after receiving ground confirmation
    """

    # If we have not triggered burn wire before, attempt to do so
    # and set bit flag 
    try:
        # Default starting values for burn() are:
        # burn_num = "1" or "2"
        # dutycycle = 0.05
        # freq = 1000
        # duration  = 1
        
        cubesat.burn("1", 0.05, 1000, 1)
        cubesat.burnedAlready = True # Set bit flag
        print("Burn wire successful!")

    # If error during burn wire usage
    except Exception as e:
        print(e)
        pass

    # Next, send message to ground station once per min for 2 hrs after deployment.
    # Prepend and append radio call sign KE8VDK
    initialMessage = "KE8VDK [Hello world, CoyoteSat here!] KE8VDK"
    startTime = time.time()
    while time.time() - startTime < 7200:
        cubesat.radio1.send(initialMessage, destination = 0xFF, keep_listening = True)
        time.sleep(60) # Sleep 60 sec.
    
    # 5 sec. buffer before exiting and starting main portion
    time.sleep(5)

############# HELPER FUNCTIONS END ############# 



############# MAIN PORTION START ############# 

time.sleep(180) # 3 min. delay after pod deployment

# If burn wire bit flag not set, then perform initial routine
if not cubesat.burnedAlready:
    startupRoutine()

# Else begin the main part of the program
print("Initial routine successful!")

# Create asyncio object
cubesat.tasko = tasko

# Dict to store scheduled objects by name
cubesat.scheduled_tasks={}

# Schedule all tasks in Tasks directory
print("Loading Tasks...", end = "")
for file in os.listdir("Tasks"):
    # Remove py extension from file name
    file = file[:-3]

    # Ignore these files
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
print("\nRunning...")
try:
    # Run tasks forever
    cubesat.tasko.run()

except Exception as e:
    # If error occurs while running main FSW, print error
    formatted_exception = traceback.format_exception(e, e, e.__traceback__)
    print(formatted_exception)
    try:
        # Increment NVM error counter
        cubesat.c_state_err+=1
        # Try logging the error in log.txt on the SD card
        cubesat.log('{},{},{}'.format(formatted_exception, cubesat.c_state_err, cubesat.c_boot))
    except:
        pass


# If all other fault-handling fails, hard reset PyCubed
hardReset()



