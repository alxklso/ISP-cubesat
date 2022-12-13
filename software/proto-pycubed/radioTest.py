import time
import os
from lib.pycubed import cubesat

"""
PyCubed script that sends data from the SD card through radio.
PyCubed radio must be transmitting to another RFM9x breakout board.
Radio sends data from file one line at a time (needs to be modified later
according to transmitter capacity).
"""

if cubesat.hardware['Radio1'] and cubesat.hardware['SDcard']:
    # If there is a radio and an SD card, access the contents of the
    # SD card and send the file data one line at a time

    # For viewing all files in SD card
    # print(os.listdir("/sd"))

    try:
        # Attempt to open file in read mode 
        # file name may need to be changed 
        file = open("/sd/new_cw_data.txt", "r")

        print("Opening file and sending data:")
        print("-"*50)
        while len(file.readline()) > 0:
            fileLine = file.readline()
            cubesat.radio1.send(fileLine)
            print(fileLine)
            time.sleep(2)
        
        print("Data sent successfully!")

    except Exception as e:
        print(e)

else:
    print("No radio or SD card found!")

print("Done.")