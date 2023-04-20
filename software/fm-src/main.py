import os, time, traceback, alarm
import lib.tasko as tasko
from lib.pycubed import cubesat


"""
FSW MAIN: Creates a queue of scheduled tasks that runs forever. Includes
a first-time startup burn-wire section, as well as batt pack voltage check.
"""

############# CONFIGURATION START ############# 

"""
IMPORTANT: Make sure to set the configuration below to the following before launch
cubesat.antenna_attached = True
cubesat.benchtop_testing = False
cubesat.burn_enabled = True
cubesat.i2c_payload = True
"""

cubesat.antenna_attached = False # IMPORTANT: Only set to true if antenna is attached
cubesat.benchtop_testing = True # IMPORTANT: Set to False when dropping off for flight
cubesat.burn_enabled = False # IMPORTANT: Only set to true if burn wire is attached
cubesat.i2c_payload = False # IMPORTANT: Set to true when you attach CW payload

############# CONFIGURATION END ############# 



############# HELPER FUNCTIONS START ############# 

def showScheduledTasks():
    """
    Shows all tasks scheduled to run and the task count. 
    Remove in flight source.
    """

    print(f"\nTasks scheduled to run (count: {len(cubesat.scheduled_tasks)})")
    print("-"*50)
    for task_key, task_value in cubesat.scheduled_tasks.items():
        print(f"{task_key} -- {str(task_value)}")


def hardReset():
    """
    If all other fault-handling fails, hard reset the PyCubed board.
    """

    # If all other fault-handling fails, hard reset the PyCubed
    print("Engaging fail-safe: hard reset")
    time.sleep(10)
    cubesat.micro.on_next_reset(cubesat.micro.RunMode.NORMAL)
    cubesat.micro.reset()


############# HELPER FUNCTIONS END ############# 



############# MAIN PORTION START #############

if not cubesat.benchtop_testing:
    time.sleep(180) # Delay after pod deployment

if not cubesat.f_burnedAlready:
    # Batt pack voltage needs to be >= 7.8V for first time startup
    if cubesat.battery_voltage >= 7.8:
        cubesat.f_lowbatt = False
        cubesat.powermode('norm')
        try:
            print(f"Pre-burn NVM bit status: {cubesat.f_burnedAlready}")
            if cubesat.burn_enabled:
                cubesat.burn("1", 0.10, 1200, 1)
            cubesat.f_burnedAlready = True  # Set bit flag
            print(f"Post-burn NVM bit status: {cubesat.f_burnedAlready}")
            time.sleep(3)
        except Exception as e:
            print(e)
    # If batteries are not sufficiently charged, enter lower power mode to charge the batteries 
    # Charge until batteries are fully charged
    else:
        print("Entering low power mode...")
        cubesat.f_lowbatt = True
        cubesat.powermode('min')
        sleep_amount = 600
        if cubesat.benchtop_testing:
            sleep_alarm = 3
        sleep_alarm = alarm.time.TimeAlarm(monotonic_time=time.monotonic() + sleep_alarm)
        # Sleeps the cubesat until the alarm sounds, then it runs main.py again
        alarm.exit_and_deep_sleep_until_alarms(sleep_alarm)
else:
    print("Startup routine successful! Starting main portion...")

    # Schedule tasks
    cubesat.tasko = tasko
    cubesat.scheduled_tasks={}

    print("Loading Tasks...", end = "")
    for file in os.listdir("Tasks"):
        file = file[:-3]

        # Ignore these files
        disabled_tasks = ["template_task","listen_task"]
        if not cubesat.i2c_payload:
            disabled_tasks.append("cw_task")
        if file in disabled_tasks or file.startswith('._'):
            continue

        # Import task file
        exec('import Tasks.{}'.format(file))
        task_obj = eval('Tasks.'+file).task(cubesat)

        # Tasks scheduled for later 
        if hasattr(task_obj, 'schedule_later') and getattr(task_obj, 'schedule_later'):
            schedule = cubesat.tasko.schedule_later
        else:
            schedule = cubesat.tasko.schedule

        cubesat.scheduled_tasks[task_obj.name]=schedule(task_obj.frequency, task_obj.main_task, task_obj.priority)

    # Show all scheduled tasks
    showScheduledTasks()

    # Driver code, runs forever
    print("\nRunning...")
    try:
        # Run tasks forever
        cubesat.tasko.run()

    except Exception as e:
        formatted_exception = traceback.format_exception(e, e, e.__traceback__)
        print(formatted_exception)
        try:
            # Increment NVM error counter
            cubesat.c_state_err+=1
            # Try logging the error in log.txt on the SD card
            cubesat.log('{},{},{}'.format(formatted_exception, cubesat.c_state_err, cubesat.c_boot))
        except:
            pass

# we shouldn't be here!
# Hard reset if all other fault-handling measures fail
hardReset()