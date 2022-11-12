# Comments: take off the mode choice part when adding it into the PyCubed FSW
# Change everything to Python3

import glob
import math
import multiprocessing
import os.path
import random
import signal
import socket
import sys
import time
from datetime import datetime

import numpy as np
import serial
import tornado.httpserver
import tornado.ioloop
import tornado.web
import tornado.websocket


# This is a Websocket server that forwards signals from the detector to any client connected.
# It requires Tornado python library to work properly.
# Please run `pip install tornado` with python of version 2.7.9 or greater to install tornado.
# Run it with `python detector-server.py`
# Written by Pawel Przewlocki (pawel.przewlocki@ncbj.gov.pl).
# Based on http://fabacademy.org/archives/2015/doc/WebSocketConsole.html


#===================== HELP =======================
# This code looks through the serial ports.
# You must select which port contains the Arduino.
# If you have problems, check the following:
# 1. Is your Arduino connected to the serial USB port?
# 2. Check that you have the correct drivers installed:
# macOS: CH340g driver (try: https://github.com/adrianmihalko/ch340g-ch34g-ch34x-mac-os-x-driver)
# Windows: no driver needed
# Linux: no driver needed


clients = []  # list of clients connected
queue = multiprocessing.Queue()  # queue for events forwarded from the device


class DataCollectionProcess(multiprocessing.Process):
    def __init__(self, queue):
        # multiprocessing.Process.__init__(self)
        self.queue = queue
        self.comport = serial.Serial(port_name_list[0])  # open the COM Port
        self.comport.baudrate = 9600  # set Baud rate
        self.comport.bytesize = 8  # Number of data bits = 8
        self.comport.parity = 'N'  # No parity
        self.p.stopbits = 1

    def close(self):
        self.comport.close()

    def nextTime(self, rate):
        return -math.log(1.0 - random.random()) / rate


def RUN(bg):
    print('Running...')
    while True:
        data = bg.comport.readline()
        bg.queue.put(str(datetime.now()) + " " + data)


class WSHandler(tornado.websocket.WebSocketHandler):
    def __init__(self, application, request, **kwargs):
        super(WSHandler, self).__init__(application, request, **kwargs)
        self.sending = False

    def open(self):
        print('New connection opened from ' + self.request.remote_ip)
        clients.append(self)
        print('%d clients connected' % len(clients))

    def on_message(self, message):
        print('message received:  %s' % message)
        if message == 'StartData':
            self.sending = True
        if message == 'StopData':
            self.sending = False

    def on_close(self):
        self.sending = False
        clients.remove(self)
        print('Connection closed from ' + self.request.remote_ip)
        print('%d clients connected' % len(clients))

    def check_origin(self, origin):
        return True


def displayAvailSerialPorts():
    print('Available serial ports:')
    for i in range(len(portsList)):
        print('[' + str(i + 1) + '] ' + str(portsList[i]))

def checkQueue():
    while not queue.empty():
        message = queue.get()
        ##sys.stdout.write('#')
        for client in clients:
            if client.sending:
                client.write_message(message)


def signal_handler(signal, frame):
    print('You pressed Ctrl+C!')
    ComPort.close()
    file.close()
    sys.exit(0)


def serial_ports():
    # Determines system OS and retrieves serial port info accordingly
    # raises EnvironmentError: on unsupported/unknown platforms
    # returns result: a list of the serial ports available on the system

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
        sys.exit(0)

    # list for storing serial port names
    portsList = []

    # adds port names to results list
    for portVal in ports:
        try:
            s = serial.Serial(portVal)
            s.close()
            portsList.append(portVal)
        except (OSError, serial.SerialException):
            pass
    # returns list of portVals, which are populated dependent on OS
    return portsList


# BEGINNING OF MAIN
# (05 Nov 2022): Changes to make for ISP mission:
# - Convert to python3.
# - Remove code accounting for using multiple CWs --> only one CW will be used.
# - Delete modes 2,3,4: only have the option to record to the computer.
# - Only have two options:
#       1 - Save data to computer
#       2 - Connect to CW server
# To do next: connect to PyCubed via UART and save to SD on there
# If the Arduino is not recognized by your MAC, make sure you have
# installed the drivers for the Arduino (CH340g driver). Windows and Linux don't need it.

print('\n             Welcome to:   ')
print('CosmicWatch: The Desktop Muon Detector\n')
print("Select an option:")
print("[1] Record data on the computer")
print("[2] Connect to server: www.cosmicwatch.lns.mit.edu")

mode = str(input("\nSelected operation: "))

# only modes able to be chosen are 1 or 2
if int(mode) not in [1, 2]:
    print('\nError: invalid selection')
    print('Exiting...')
    sys.exit()

# if all is valid, retrieve serial port connections from OS and
# display serial port connections in console
portsList = serial_ports()
displayAvailSerialPorts(portsList)

# port selection defined by user.
# original code allowed for multiple CWs, we are only allowing for one
portSelection = input("Selected Arduino port: ")

port_name_list = []

for i in range(len(portSelection)):
    port_name_list.append(str(portsList[int(portSelection[i]) - 1]))


# display selected port
print("The selected port is: ")
print('\t[' + str(portSelection) + ']' + port_name_list[0])

# MODE 1: Record data to the computer. CW data is recorded and stored in a location specified by
# the user. Name of the file can be customized as well.
if mode == 1:
    cwd = os.getcwd()  # get current working dir
    fileName = input("Enter file name (default: " + cwd + "/CW_data.txt):") # user-defined filename
    detector_name_list = []

    # default name is CWD + /CW_data.txt
    if fileName == '':
        fileName = cwd + "/CW_data.txt"

    print('Saving data to: ' + fileName)

    # creates a singleton np array populated with 1
    ComPort_list = np.ones(1)

     # iterate through n detectors
    for i in range(nDetectors):
        signal.signal(signal.SIGINT, signal_handler)
        globals()['Det%s' % str(0)] = serial.Serial(str(port_name_list[0]))
        globals()['Det%s' % str(0)].baudrate = 9600
        globals()['Det%s' % str(0)].bytesize = 8  # Number of data bits = 8
        globals()['Det%s' % str(0)].parity = 'N'  # No parity
        globals()['Det%s' % str(0)].stopbits = 1

        time.sleep(1)
        # globals()['Det%s' % str(i)].write('write')

        counter = 0

        header1 = str(globals()['Det%s' % str(i)].readline())  # Wait and read data
        if ('SD initialization failed' in header1):
            print('...SDCard.ino detected.')
            print('...SDcard initialization failed.')
            # This happens if the SDCard.ino is uploaded but it doesn't see an sdcard.
            header1a = str(globals()['Det%s' % str(i)].readline())
            header1 = str(globals()['Det%s' % str(i)].readline())
        if ('CosmicWatchDetector' in header1):
            print('...SDCard.ino code detected.')
            print('...SDcard intialized correctly.')
            # This happens if the SDCar.ino is uploaded and it sees an sdcard.
            header1a = str(globals()['Det%s' % str(i)].readline())
            globals()['Det%s' % str(i)].write('write')
            header1b = str(globals()['Det%s' % str(i)].readline())
            header1 = str(globals()['Det%s' % str(i)].readline())
        # header1 = globals()['Det%s' % str(i)].readline()
        header2 = str(globals()['Det%s' % str(i)].readline())  # Wait and read data
        header3 = str(globals()['Det%s' % str(i)].readline())  # Wait and read data
        header4 = str(globals()['Det%s' % str(i)].readline())  # Wait and read data
        header5 = str(globals()['Det%s' % str(i)].readline())  # Wait and read data

        det_name = str(globals()['Det%s' % str(i)].readline()).replace('\r\n', '')
        # print(det_name)
        if 'Device ID: ' in det_name:
            det_name = det_name.split('Device ID: ')[-1]
        detector_name_list.append(det_name)  # Wait and read data

    file = open(fileName, "w")
    file.write(header1)
    file.write(header2)
    file.write(header3)
    file.write(header4)
    file.write(header5)

    string_of_names = ''
    print("\n-- Detector Names --")
    # print(detector_name_list)
    for i in range(len(detector_name_list)):
        print(detector_name_list[i])
        if '\xff' in detector_name_list[i] or '?' in detector_name_list[i]:
            print('--- Error ---')
            print('You should name your CosmicWatch Detector first.')
            print('Simply change the DetName variable in the Naming.ino script,')
            print('and upload the code to your Arduino.')
            print('Exiting ...')

    print("\nTaking data ...")
    print("Press ctl+c to terminate process")

    if nDetectors > 1:
        for i in range(nDetectors):
            string_of_names += detector_name_list[i] + ', '
    else:
        string_of_names += detector_name_list[0]

    # print(string_of_names)
    file.write('Device ID(s): ' + string_of_names)
    file.write('\n')
    # detector_name = ComPort.readline()    # Wait and read data
    # file.write("Device ID: "+str(detector_name))

    while True:
        for i in range(nDetectors):
            if globals()['Det%s' % str(i)].inWaiting():
                data = str(globals()['Det%s' % str(i)].readline()).replace('\r\n', '')  # Wait and read data
                file.write(str(datetime.now()) + " " + data + " " + detector_name_list[i] + '\n')
                globals()['Det%s' % str(i)].write('got-it'.encode())

    for i in range(nDetectors):
        globals()['Det%s' % str(i)].close()
    file.close()


# MODE 2: Connect to the CW server. Allows real-time data plotting on www.cosmicwatch.lns.mit.edu.
if mode == 2:
    bg = DataCollectionProcess(queue)
    # bg.daemon = True
    # bg.start()
    thread.start_new_thread(RUN, (bg,))
    # p=multiprocessing.Process(target=RUN)
    # p.start()
    # server stuff
    application = tornado.web.Application(
        handlers=[(r'/', WSHandler)]
    )
    http_server = tornado.httpserver.HTTPServer(application)
    port = 9090
    http_server.listen(port)
    myIP = socket.gethostbyname(socket.gethostname())
    print('CosmicWatch detector server started at %s:%d' % (myIP, port))
    print('You can now connect to your device using http://cosmicwatch.lns.mit.edu/')
    mainLoop = tornado.ioloop.IOLoop.instance()
    # in the main loop fire queue check each 100ms
    try:
        scheduler = tornado.ioloop.PeriodicCallback(checkQueue, 100, io_loop=mainLoop)
    except:
        # io_loop arguement was removed in version 5.x of Tornado.
        scheduler = tornado.ioloop.PeriodicCallback(checkQueue, 100)
        scheduler.start()
        # start the loop
        mainLoop.start()