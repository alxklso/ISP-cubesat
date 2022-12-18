from lib.pycubed import cubesat
import time, os

"""
PyCubed script that sends data from the SD card through radio.
PyCubed radio must be transmitting to another RFM9x breakout board.
"""

if cubesat.hardware['Radio1'] and cubesat.hardware['SDcard']:
    # If there is a radio and an SD card, access the contents of the
    # SD card and send a couple lines
    # print(os.listdir("/sd"))

    try:
        file_data = open("/sd/cw_data.txt", "r").readline()
        print("File data:\n")
        print(file_data)
    
    except Exception as e:
        print(e)

    

else:
    print("No radio found!")