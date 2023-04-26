import os, time, traceback, alarm
import lib.tasko as tasko
from lib.pycubed import cubesat


"""
FSW MAIN: Creates a queue of scheduled tasks that runs forever. Includes
a first-time startup burn-wire section, as well as batt pack voltage check.
After first-time burn-wire activation, main is entered repeatedly forever.
Includes board hard-reset if all other fault-handling measures fail.
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



if not cubesat.benchtop_testing:
    time.sleep(180) # 3 min delay after pod deployment

if not cubesat.f_burnedAlready:
    # Batt pack voltage needs to be >= 7.8V for first time startup
    # This section of the code is only ever entered once. Once antennas 
    # are deployed, main is run perpetually.
    if cubesat.battery_voltage >= 7.8:
        try:
            print(f"Pre-burn NVM bit status: {cubesat.f_burnedAlready}")
            if cubesat.burn_enabled:
                cubesat.burn("1", 0.10, 1200, 1)
            cubesat.f_burnedAlready = True  # Set bit flag
            print(f"Post-burn NVM bit status: {cubesat.f_burnedAlready}")
            time.sleep(3)
            cubesat.f_lowbatt = False
            cubesat.powermode("norm")
        except Exception as e:
            print(e)
    # If batteries are not sufficiently charged, enter lower power mode to charge the batteries 
    # Charge until batteries are fully charged
    else:
        print("Entering low power mode...")
        cubesat.f_lowbatt = True
        cubesat.powermode("min")
        sleep_amount = 600
        if cubesat.benchtop_testing:
            sleep_alarm = 3
        sleep_alarm = alarm.time.TimeAlarm(monotonic_time=time.monotonic() + sleep_alarm)
        # Sleeps the cubesat until the alarm sounds, then it runs main.py again
        alarm.exit_and_deep_sleep_until_alarms(sleep_alarm)
else:
    print("Startup routine successful! Starting main portion...")

    # If booting up for first or second time, send identifier beacon
    # Include couple boots for accidental measure
    # TODO: Fix this identifier beacon portion, boot count would need to be fixed
    if cubesat.c_boot < 3 and cubesat.antenna_attached: 
        start_time = time.time()
        while (time.time() < start_time+(60*60)):
            print("Sending identifier beacon...")
            cubesat.radio1.send("KE8VDKCoyoteSat boot up successful!\0")
            time.sleep(60)

    # Schedule tasks
    cubesat.tasko = tasko
    cubesat.scheduled_tasks={}

    print("Loading Tasks...", end = "")
    for file in os.listdir("Tasks"):
        file = file[:-3]

        # Ignore these files
        disabled_tasks = ["template_task", "listen_task"]
        if not cubesat.i2c_payload or not cubesat.antenna_attached:
            disabled_tasks.append("cw_task")
        if file in disabled_tasks or file.startswith('._'):
            continue

        # Import task file
        exec(f"import Tasks.{file}")
        task_obj = eval("Tasks." + file).task(cubesat)

        # Tasks scheduled for later 
        if hasattr(task_obj, "schedule_later") and getattr(task_obj, "schedule_later"):
            schedule = cubesat.tasko.schedule_later
        else:
            schedule = cubesat.tasko.schedule

        cubesat.scheduled_tasks[task_obj.name]=schedule(task_obj.frequency, task_obj.main_task, task_obj.priority)

    if cubesat.benchtop_testing:
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
            # Increment NVM error counter and log error in log.txt on SD card
            cubesat.c_state_err+=1
            cubesat.log(f"{formatted_exception},{cubesat.c_state_err},{cubesat.c_boot}")
        except:
            pass

# Hard reset if all other fault-handling measures fail
hardReset()