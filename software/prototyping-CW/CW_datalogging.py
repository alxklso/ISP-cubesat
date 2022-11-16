import serial,time,sys,glob


def serial_ports():
    #This is a function that gets a list of port names from the OS and returns it

    # Check which OS the user is running 
    if sys.platform.startswith('win'):
        # windows OS
        ports = ['COM%s' % (i + 1) for i in range(256)]
    elif sys.platform.startswith('linux') or sys.platform.startswith('cygwin'):
        # linuxOS or windows Cygwin
        # this excludes your current terminal "/dev/tty"
        ports = glob.glob('/dev/tty[A-Za-z]*')
    elif sys.platform.startswith('darwin'):
        # macOS
        ports = glob.glob('/dev/tty.*')
    else:
        # if OS cannot be detected, raise EnvironmentError and exit
        raise EnvironmentError('Unsupported platform')

    # List for storing serial port names
    portsList = []

    # Adds port names to portsList
    for portVal in ports:
        try:
            s = serial.Serial(portVal)
            s.close()
            portsList.append(portVal)
        except (OSError, serial.SerialException):
            pass

    # Returns list of port names
    return portsList


def displayAvailSerialPorts(portsList):
    """
    Function that displays the available serial ports
    in the console.
    """
    print('Available serial ports:')
    for i in range(len(portsList)):
        print('[' + str(i + 1) + '] ' + str(portsList[i]))


# Driver Code
def main():

    # Get list of serial ports and display them as a menu
    port_list = serial_ports()
    displayAvailSerialPorts(port_list)

    # Ask user to choose a serial port from the menu
    portSelection = input("Selected Arduino port: ")

    # Get the port name
    portName = str(port_list[int(portSelection) - 1])

    # Instance of serial, setting serial parameters
    # port, baudrate, timeout
    arduino = serial.Serial(port=portName, baudrate=9600, timeout=.1)

    # Only display data from serial port device in console if the
    # raw byte string is non-empty
    while True:
        time.sleep(0.05)
        data = arduino.readline()
        if len(data) > 0:
            print(str(data.decode("utf-8")))


# Run main program
main()