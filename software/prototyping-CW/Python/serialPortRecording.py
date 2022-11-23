import serial
import time

"""
This is a script that listens to the serial port and displays the 
data in terminal. The data is sent from the Cosmic Watch sensor via 
the UART pins on the Arduino Nano board to the serial port on your
computer.
"""

def displayMenu():
    """Ask the user if they would like to file or 
    only display to console
    """
    print("\nCosmic Watch to Serial Port Script")
    print("-"*40)
    print("Please select an option below:")
    print("1. Display in console")
    print("2. Write to file")

# Driver code
def main():
    # Connect to serial port
    ser = serial.Serial("/dev/tty.usbserial-0001")

    # Display menu and ask for user input
    displayMenu()
    selection = int(input("\nSelection: "))
    print("\n") # Space

    # Respond to user input
    if (selection == 1):
        # Display to console
        print("Displaying to console...")
        while True:
            serBytesDecoded = ser.readline().decode("utf-8") # Read in and decode data
            print(serBytesDecoded) 

    elif selection == 2:
        # Attempt to write to file
        fileName = input("Enter name of file (saved as txt): ")
        
        try: 
            print("Attempting to write to file...")
            f = open(fileName + ".txt", "a") # Append mode 

            while True:
                serBytesDecoded = ser.readline().decode("utf-8") # Read in and decode data
                print(serBytesDecoded) 
                f.write(serBytesDecoded)
        
        # If file cannot be opened
        except:
            print("Exiting...")


    # For separating data 
    ser.flushInput() 

main()