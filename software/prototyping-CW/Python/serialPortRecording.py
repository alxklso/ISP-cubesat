import serial

"""
This is a script that listens to the serial port and displays the 
data in terminal. The data is sent from the Cosmic Watch sensor via 
the UART pins on the Arduino Nano board to the serial port on your
computer.
"""

# Select correct port 
ser = serial.Serial("/dev/tty.usbserial-0001")
ser.flushInput() # for separating data 

while True:
    try:
        ser_bytes = ser.readline()
        print(ser_bytes.decode("utf-8"))

    except:
        print("Keyboard Interrupt")
        break


