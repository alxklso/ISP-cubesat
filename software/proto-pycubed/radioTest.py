"""
For sending or receiving messages using the PyCubed radio
"""
import time, digitalio, board
import lib.pycubed_rfm9x as pycubed_rfm9x
from lib.pycubed import cubesat 

# NOTE: ANTENNA MUST BE ATTACHED BEFORE DOING ANY RADIO WORK
# MANUALLY CHANGE THE ANTENNA_ATTACHED VARIABLE BELOW TO TRUE AFTER 
# PHYSICALLY ATTACHING AN ANTENNA. YOU CAN OTHERWISE FRY THE BOARD!

# TODO: add functionality to allow the user to select radio 1 or radio 2

# Function to explicitly check if the antenna is attached to the PyCubed
def check_antenna():
    is_antenna_attached = input("Is the antenna attached to the board? (y/n) ")
    if is_antenna_attached == "y":
        return True
    return False


def init_radio():
    # Try radio 2 init
    try:
        # Define radio 2
        _rf_cs2 = digitalio.DigitalInOut(board.RF2_CS)
        _rf_rst2 = digitalio.DigitalInOut(board.RF2_RST)
        #cubesat.enable_rf = digitalio.DigitalInOut(board.EN_RF)
        cubesat.radio2_DIO0=digitalio.DigitalInOut(board.RF2_IO0)
        #cubesat.enable_rf.switch_to_output(value=False) # if U21
        _rf_cs2.switch_to_output(value=True)
        _rf_rst2.switch_to_output(value=True)
        cubesat.radio2_DIO0.switch_to_input()


        cubesat.radio2 = pycubed_rfm9x.RFM9x(cubesat.spi, _rf_cs2, _rf_rst2,
            433.0, code_rate=8, baudrate=1320000)
        # Default LoRa Modulation Settings
        # Frequency: 433 MHz, SF7, BW125kHz, CR4/8, Preamble=8, CRC=True
        cubesat.radio2.dio0=cubesat.radio2_DIO0
        cubesat.radio2.enable_crc=True
        cubesat.radio2.ack_delay=0.2
        cubesat.radio2.sleep()
        cubesat.hardware["Radio2"] = True
        print("Radio 2 initialized properly!\n")

    except Exception as e:
        print("Error initializing radio 2")
        print(e, end = "\n")


# Transmit function that sends user's message in infinite loop
# with counter attached
def transmit_test(message):
    try: 
        i = 0
        while True:
            cubesat.radio2.send(str(i) + " " + message + "                                                                                                   ")
            print(str(i) + " - " + message)
            i+= 1
            time.sleep(1)

    except Exception as e:
        print(e)
        time.sleep(1)


# Receive function that listens in infinite loop and prints 
# received messages to the console
def receive_test():
    try:
        while True:
            packet = cubesat.radio2.receive()

            if packet is None:
                pass
            else:
                print(f"Received (raw bytes): {packet}")

    except Exception as e:
        print(e)

# Main menu portion, allows user to select transmit or receive
def main():
    print("\nPyCubed Radio Testing")
    print("-"*50, end = "\n")

    antenna_attached = check_antenna()

    if antenna_attached:
        # If the antenna is attached, initialize radio and proceed
        init_radio()

        choice = input("Would you like to transmit (\"t\") or receive (\"r\")? ")
            
        if choice == "t":
            message = input("Enter message to send: ")
            print(f"Sending message: \"{message}\" ... ")
            transmit_test(message)
        if choice == "r":
            print("Listening for messages...")
            receive_test()
        else: 
            print("Invalid choice!")
            print("Exiting...")

    # If the antenna is not attached        
    print("Attach antenna and soft reset!")


# run main
main()