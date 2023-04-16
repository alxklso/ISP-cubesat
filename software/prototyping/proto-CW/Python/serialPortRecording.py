# Viewing all serial ports command: ls /dev/tty.*

import serial

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

    """
    This is a script that listens to the serial port and displays to the 
    data in the console with the option of creating and writing data to a
    file. The data is sent from the Cosmic Watch sensor via the UART pins
    on the Arduino Nano board to the serial port on your computer.

    Notes:
    - Serial port currently in place is for Mac, may need to change depending 
    on OS and computer
    - A USB-TTL adapter, breadboard, and extra wires were used to connect the 
    Nano to the computer. 
    """
    
    # Connect to serial port (change val according to OS and device)
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