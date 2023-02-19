# New and improved main.py for checking CubeSat's overall health
# and status of subsystems. To be run after vibration testing.
# Modified by: ISP Software Team

# Common CircuitPython Libs
import time, asyncio
import board, microcontroller
import busio, sys
from storage import mount,umount,VfsFat
from analogio import AnalogIn
import lib.tasko as tasko 
import digitalio, sdcardio, pwmio

# Hardware Specific Libs
import pycubed_rfm9x # Radio
import neopixel # RGB LED
import bq25883 # USB Charger
import adm1176 # Power Monitor

# Common CircuitPython Libs
from os import listdir, stat, statvfs, mkdir, chdir
from bitflags import bitFlag,multiBitFlag,multiByte
from micropython import const


#1. Define + initialize hardware

# NVM register numbers
_BOOTCNT  = const(0)
_VBUSRST  = const(6)
_STATECNT = const(7)
_TOUTS    = const(9)
_GSRSP    = const(10)
_ICHRG    = const(11)
_FLAG     = const(16)

SEND_BUFF = bytearray(252)

class Satellite:
    # General NVM counters
    c_boot      = multiBitFlag(register = _BOOTCNT, lowest_bit = 0, num_bits = 8)
    c_vbusrst   = multiBitFlag(register = _VBUSRST, lowest_bit = 0, num_bits = 8)
    c_state_err = multiBitFlag(register = _STATECNT,lowest_bit = 0, num_bits = 8)
    c_gs_resp   = multiBitFlag(register = _GSRSP,   lowest_bit = 0, num_bits = 8)
    c_ichrg     = multiBitFlag(register = _ICHRG,   lowest_bit = 0, num_bits = 8)

    # Define NVM flags
    f_lowbatt  = bitFlag(register = _FLAG, bit=0)
    f_solar    = bitFlag(register = _FLAG, bit=1)
    f_gpson    = bitFlag(register = _FLAG, bit=2)
    f_lowbtout = bitFlag(register = _FLAG, bit = 3)
    f_gpsfix   = bitFlag(register = _FLAG, bit = 4)
    f_shtdwn   = bitFlag(register = _FLAG, bit = 5)

    def __init__(self):
        #Big init routine as the whole board is brought up.
        self.BOOTTIME = const(time.time())
        self.data_cache = {}
        self.filenumbers = {}
        self.vlowbatt = 6.0
        self.send_buff = memoryview(SEND_BUFF)
        self.debug = True
        self.micro = microcontroller
        self.hardware = {'Radio2': False, 'SDcard': False, 'WDT': False, 'USB': False, 'PWR': False}
        
        # Define burn wires:
        self._relayA = digitalio.DigitalInOut(board.RELAY_A)
        self._relayA.switch_to_output(drive_mode = digitalio.DriveMode.OPEN_DRAIN)
        self._resetReg = digitalio.DigitalInOut(board.VBUS_RST)
        self._resetReg.switch_to_output(drive_mode = digitalio.DriveMode.OPEN_DRAIN)

        # Define battery voltage
        self._vbatt = AnalogIn(board.BATTERY)

        # Define MPPT charge current measurement
        self._ichrg = AnalogIn(board.L1PROG)
        self._chrg  = digitalio.DigitalInOut(board.CHRG)
        self._chrg.switch_to_input()

        # Define SPI, I2C, UART
        self.i2c1 = busio.I2C(board.SCL, board.SDA)
        self.spi  = board.SPI()
        self.uart = busio.UART(board.TX, board.RX)

        # Define filesystem stuff
        self.logfile = '/log.txt'

        # Define radio
        _rf_cs2 = digitalio.DigitalInOut(board.RF2_CS)
        _rf_rst2 = digitalio.DigitalInOut(board.RF2_RST)
        self.enable_rf = digitalio.DigitalInOut(board.EN_RF)
        self.radio2_DIO0 = digitalio.DigitalInOut(board.RF2_IO0)
        # self.enable_rf.switch_to_output(value = False) # if U21
        self.enable_rf.switch_to_output(value = True) # if U7
        _rf_cs2.switch_to_output(value = True)
        _rf_rst2.switch_to_output(value = True)
        self.radio2_DIO0.switch_to_input()

        # Initialize SD card (always init SD before anything else on spi bus)
        try:
            # Baud rate depends on the card, 4MHz should be safe
            _sd = sdcardio.SDCard(self.spi, board.SD_CS, baudrate = 4000000)
            _vfs = VfsFat(_sd)
            mount(_vfs, '/sd')
            self.fs=_vfs
            sys.path.append('/sd')
            self.hardware['SDcard'] = True
            self.logfile = '/sd/log.txt'
        except Exception as e:
            if self.debug: print('[ERROR][SD Card]', e)

        # Initialize radio #2 - UHF
        try:
            self.radio2 = pycubed_rfm9x.RFM9x(self.spi, _rf_cs2, _rf_rst2,
                433.0, code_rate = 8, baudrate = 1320000)
            # Default LoRa Modulation Settings
            # Frequency: 433 MHz, SF7, BW125kHz, CR4/8, Preamble = 8, CRC = True
            self.radio2.dio0 = self.radio2_DIO0
            self.radio2.enable_crc = True
            self.radio2.ack_delay = 0.2
            self.radio2.sleep()
            self.hardware['Radio2'] = True
        except Exception as e:
            if self.debug: print('[ERROR][RADIO 2]',e)

        # Initialize Neopixel
        try:
            self.neopixel = neopixel.NeoPixel(board.NEOPIXEL, 1, brightness = 0.2, pixel_order = neopixel.GRB)
            self.neopixel[0] = (0,0,0)
            self.hardware['Neopixel'] = True
        except Exception as e:
            if self.debug: print('[WARNING][Neopixel]',e)

        # Initialize USB charger
        try:
            self.usb = bq25883.BQ25883(self.i2c1)
            self.usb.charging = False
            self.usb.wdt = False
            self.usb.led = False
            self.usb.charging_current = 8 #400mA
            self.usb_charging = False
            self.hardware['USB'] = True
        except Exception as e:
            if self.debug: print('[ERROR][USB Charger]',e)

        # Initialize Power Monitor
        try:
            self.pwr = adm1176.ADM1176(self.i2c1)
            self.pwr.sense_resistor = 1
            self.hardware['PWR'] = True
        except Exception as e:
            if self.debug: print('[ERROR][Power Monitor]', e)

        # set PyCubed power mode
        self.power_mode = 'normal'

    def reinit(self,dev):
        dev = dev.lower()
        if dev == 'pwr':
            self.pwr.__init__(self.i2c1)
        elif dev == 'usb':
            self.usb.__init__(self.i2c1)
        else:
            print('Invalid Device? ->', dev)

    @property
    def RGB(self):
        return self.neopixel[0]
    @RGB.setter
    def RGB(self,value):
        if self.hardware['Neopixel']:
            try:
                self.neopixel[0] = value
            except Exception as e:
                print('[WARNING]', e)

    @property
    def charge_batteries(self):
        if self.hardware['USB']:
            return self.usb_charging
    @charge_batteries.setter
    def charge_batteries(self, value):
        if self.hardware['USB']:
            self.usb_charging = value
            self.usb.led = value
            self.usb.charging = value

    @property
    def battery_voltage(self):
        _vbat = 0
        for _ in range(50):
            _vbat += self._vbatt.value * 3.3 / 65536
        _voltage = (_vbat/50)*(316+110)/110 # 316/110 voltage divider
        return _voltage # volts

    @property
    def system_voltage(self):
        if self.hardware['PWR']:
            try:
                return self.pwr.read()[0] # volts
            except Exception as e:
                print('[WARNING][PWR Monitor]', e)
        else:
            print('[WARNING] Power monitor not initialized')

    @property
    def current_draw(self):
        """
        current draw from batteries
        NOT accurate if powered via USB
        """
        if self.hardware['PWR']:
            idraw = 0
            try:
                for _ in range(50): # average 50 readings
                    idraw += self.pwr.read()[1]
                return (idraw/50)*1000 # mA
            except Exception as e:
                print('[WARNING][PWR Monitor]', e)
        else:
            print('[WARNING] Power monitor not initialized')

    @property
    def charge_current(self):
        """
        LTC4121 solar charging IC with charge current monitoring
        See Programming the Charge Current section
        """
        _charge = 0
        if self.solar_charging:
            _charge = self._ichrg.value * 3.3 / 65536
            _charge = ((_charge*988)/3010)*1000
        return _charge # mA

    @property
    def solar_charging(self):
        return not self._chrg.value

    @property
    def reset_vbus(self):
        # unmount SD card to avoid errors
        if self.hardware['SDcard']:
            try:
                umount('/sd')
                self.spi.deinit()
                time.sleep(3)
            except Exception as e:
                print('vbus reset error?', e)
                pass
        self._resetReg.drive_mode = digitalio.DriveMode.PUSH_PULL
        self._resetReg.value = 1

    def log(self, msg):
        if self.hardware['SDcard']:
            with open(self.logfile, 'a+') as f:
                t = int(time.monotonic())
                f.write('{}, {}\n'.format(t,msg))

    def print_file(self, filedir = None, binary = False):
        if filedir == None:
            return
        print('\n--- Printing File: {} ---'.format(filedir))
        if binary:
            with open(filedir, 'rb') as file:
                print(file.read())
                print('')
        else:
            with open(filedir, 'r') as file:
                for line in file:
                    print(line.strip())

    def timeout_handler(self):
        print('Incrementing timeout register')
        if (self.micro.nvm[_TOUTS] + 1) >= 255:
            self.micro.nvm[_TOUTS] = 0
            # soft reset
            self.micro.on_next_reset(self.micro.RunMode.NORMAL)
            self.micro.reset()
        else:
            self.micro.nvm[_TOUTS] += 1

    def powermode(self, mode):
        """
        Configure the hardware for minimum or normal power consumption
        Add custom modes for mission-specific control
        """
        if 'min' in mode:
            self.RGB = (0,0,0)
            self.neopixel.brightness = 0
            if self.hardware['Radio2']:
                self.radio2.sleep()
            self.enable_rf.value = False
            if self.hardware['PWR']:
                self.pwr.config('V_ONCE,I_ONCE')
            self.power_mode = 'minimum'

        elif 'norm' in mode:
            self.enable_rf.value = True
            if self.hardware['PWR']:
                self.pwr.config('V_CONT,I_CONT')
            self.power_mode = 'normal'
            # don't forget to reconfigure radios, gps, etc...

    def new_file(self, substring, binary = False):
        """
        substring something like '/data/DATA_'
        directory is created on the SD!
        int padded with zeros will be appended to the last found file
        """
        if self.hardware['SDcard']:
            ff = ''
            n = 0
            _folder = substring[:substring.rfind('/')+1]
            _file = substring[substring.rfind('/')+1:]
            print('Creating new file in directory: /sd{} with file prefix: {}'.format(_folder,_file))
            try: chdir('/sd'+_folder)
            except OSError:
                print('Directory {} not found. Creating...'.format(_folder))
                try: mkdir('/sd'+_folder)
                except Exception as e:
                    print(e)
                    return None
            for i in range(0xFFFF):
                ff = '/sd{}{}{:05}.txt'.format(_folder, _file, (n+i)%0xFFFF)
                try:
                    if n is not None:
                        stat(ff)
                except:
                    n = (n+i)%0xFFFF
                    # print('file number is',n)
                    break
            print('creating file...',ff)
            if binary: b = 'ab'
            else: b = 'a'
            with open(ff, b) as f:
                f.tell()
            chdir('/')
            return ff

    def burn(self, burn_num, dutycycle = 0, freq = 1000, duration = 1):
        """
        Operate burn wire circuits. Wont do anything unless the a nichrome burn wire
        has been installed.

        IMPORTANT: See "Burn Wire Info & Usage" of https://pycubed.org/resources
        before attempting to use this function!

        burn_num:  (string) which burn wire circuit to operate, must be either '1' or '2'
        dutycycle: (float) duty cycle percent, must be 0.0 to 100
        freq:      (float) frequency in Hz of the PWM pulse, default is 1000 Hz
        duration:  (float) duration in seconds the burn wire should be on
        """
        # convert duty cycle % into 16-bit fractional up time
        dtycycl = int((dutycycle/100)*(0xFFFF))
        print('----- BURN WIRE CONFIGURATION -----')
        print('\tFrequency of: {}Hz\n\tDuty cycle of: {}% (int:{})\n\tDuration of {}sec'.format(freq,(100*dtycycl/0xFFFF),dtycycl,duration))
        # create our PWM object for the respective pin
        # not active since duty_cycle is set to 0 (for now)
        if '1' in burn_num:
            burnwire = pwmio.PWMOut(board.BURN1, frequency = freq, duty_cycle = 0)
        elif '2' in burn_num:
            burnwire = pwmio.PWMOut(board.BURN2, frequency = freq, duty_cycle = 0)
        else:
            return False
        # Configure the relay control pin & open relay
        self._relayA.drive_mode = digitalio.DriveMode.PUSH_PULL
        self._relayA.value = 1
        self.RGB = (255,0,0)
        # Pause to ensure relay is open
        time.sleep(0.5)
        # Set the duty cycle over 0%
        # This starts the burn!
        burnwire.duty_cycle = dtycycl
        time.sleep(duration)
        # Clean up
        self._relayA.value = 0
        burnwire.duty_cycle = 0
        self.RGB = (0,0,0)
        burnwire.deinit()
        self._relayA.drive_mode = digitalio.DriveMode.OPEN_DRAIN
        return True

# 2. Getting metrics
def metrics(self): 
    # Battery voltage
    batt_volt_check = input('Check battery voltage? (y/n): ')
    if batt_volt_check == 'y':
        print('Checking battery voltage...')
        try: 
            bat_volt = self.battery_voltage()
            print('Battery voltage: {}'.format(bat_volt))
        except:
            print('Battery voltage failed')
    
    # System voltage
    syst_volt_check = input('Check system voltage? (y/n): ')
    if syst_volt_check == 'y':
        print('Checking system voltage...')
        try:
            syst_volt = self.system_voltage()
            print('System voltage: {}'.format(syst_volt))
        except:
            print('System voltage failed')

    # Current draw from batteries 
    curr_draw_check = input('Check current draw? (y/n): ')
    if curr_draw_check == 'y':
        print('Checking current draw...')
        try: 
            curr_draw = self.current_draw()
            print('Current draw: {}'.format(curr_draw))
        except:
            print('Current draw failed')

    # Charge current 
    charge_curr_check = input('Check charge current? (y/n): ')
    if charge_curr_check == 'y':
        print('Checking charge current...')
        try: 
            charge_curr = self.charge_current()
            print('Charge current: {}'.format(charge_curr))
        except:
            print('Charge current failed')

# 3. Running tasks
def tasks(self):
    # Blink Neopixel for five seconds
    blink = input('Check neopixel blink? (y/n): ')
    if blink == 'y':
        print('Blinking for 5 seconds...')
        try: 
            start = time.time()
            while time.time() - start < 5:
                self.RGB(True)
                time.sleep(0.1)
                self.RGB(False)
                time.sleep(0.1)
        except:
            print('Blinking neopixel failed')
    
    # Activate burn wire to deploy antenna
    burning = input('Activate burn wire? (y/n): ')
    if burning == 'y':
        print('Burning...')
        try: 
            burn_num = 1
            #burn_num = 2
            self.burn(burn_num, dutycycle = 0, freq = 1000, duration = 1) 
        except:
            print('Burn wire failed')

    # Write data to file and save to SD card
    write = input('Write data to SD card file? (y/n): ')
    if write == 'y':
        # If SD card does not exist
        if not self.hardware['SDcard']:
            print('No SD card detected')
        print('SD card found! Attempting to write to file...')
        try:
            with open('/sd/test.txt', 'w') as fp:
                # Attempt to write to file
                fp.write('Testing testing 1 2 3')
                print('Written to file successfully!')
                print('Testing testing 1 2 3')
        except Exception as e:
            print(e)

    # Attempt to take data from the SD card and send it via radio 
    # If data cannot be retrieved from the SD card, send a couple test strings
    take = input('Send SD card data via radio? (y/n): ')
    if take == 'y':
        #if radio2 exists
        if self.hardware['Radio2']:
            print('Radio2 found! Attempting to find SD card...')
            #if SD card exists
            if self.hardware['SDcard']:
                print('SD card found! Attempting to find radio...')
                try:
                    with open('/sd/test.txt', 'r') as fp:
                        print('File opened, now sending data...')
                        while len(fp.readline()) > 0:
                            fileLine = fp.readline()
                            self.radio2.send(fileLine)
                            print(fileLine)
                            time.sleep(2)                
                        print('Data sent successfully!')
                except Exception as e:
                    print(e)
            else: 
                print('Could not find SD card. Sending test string over radio')
                start = time.time()
                while time.time() - start < 2: # Sending for 2 seconds
                    self.radio2.send('Testing radio 1 2 3\n')
                    time.sleep(0.25)
                print('Strings sent successfully!')
        else:
            print('Could not find radio2 -> cannot send files')
    
    # Attempt to receive data from another radio (other radio will be programmed to send a message)
    receive = input('Receive data from another radio? (y/n): ')
    if receive == 'y':
        if self.hardware['Radio2']:
            print('Radio2 found! Attempting to find SD card...')
            start = time.time()
            try:
                while time.time() - start < 20: # Listen for 20 seconds
                    packet = self.radio2.receive()
                    if packet is not None:
                        print('Received (raw bytes): {0}'.format(packet))
                        packet_text = str(packet, 'ascii')
                        print('Received (ASCII): {0}'.format(packet_text))
                    else:
                        print('Received nothing! Listening again...')
            except Exception as e:
                print(e)
        else:
            print('Could not find radio2 -> cannot receive data')

try:
    cubesat = Satellite()
    cubesat.metrics()
    cubesat.tasks()
    print('CubeSat testing complete, everything works')
except:
    print('CubeSat testing failed')