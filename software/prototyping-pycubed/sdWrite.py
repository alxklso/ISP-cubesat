# View all serial port connections: ls /dev/tty.*
# Enter REPL for PyCubed: screen /dev/tty.[serial port ID]
# NOTE: MUST DRAG AND DROP THIS FILE TO PYCUBED DRIVE WHEN PLUGGED IN
# BEFORE RUNNING. THIS FILE WILL NOT RUN IF ACCESSED FROM LOCAL GIT REPO CLONE

from lib.pycubed import cubesat
import time, busio, board  

# Driver code
def main():
    """
    This is a script that records CW data on the PyCubed's SD card. 
    """
    # If SD card does not exist
    if not cubesat.hardware['SDcard']:
        cubesat.RGB=(255,0,0) # LED turns red
        print('No SD Card Detected. Press Ctrl+C to halt')
        while True:
            time.sleep(1)

    print("SD card found! Attempting to write to file...")
    fp = open("/sd/test.txt", "w") # Create the test.txt on the PyCubed SD card

    try:
        # UART setup
        uart2 = busio.UART(board.TX2, board.RX2)

        while True:
            data = uart2.read()
            if data:
                # if buffer length is nonzero (there is data), decode
                # and print to console
                dataDecoded = data.decode("utf-8")
                try:
                    # attempt to write to file 
                    print(dataDecoded)
                    fp.write(dataDecoded)
                    print("Written to file successfully!")
                except:
                    # if can't write to file, display to console
                    print("Could not write to file.")
                    print(dataDecoded)
            else:
                # if no data can be heard from UART pins
                print("No data detected!")

    # If there is some error display it to console
    except Exception as e:
        print(e)
        fp.close()

main()
