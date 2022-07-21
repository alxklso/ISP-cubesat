# file that uses the ALSPT19 Light Sensor
# to detect ambient light
import time
import board
from digitalio import DigitalInOut, Direction, Pull
from analogio import AnalogIn
pin = AnalogIn(board.A1)


def get_voltage(pin):
	return (pin.value * 3.3) / 65536
while True:
    print("Voltage reading: " + str(get_voltage(pin)))
    #print(pin.value)
    time.sleep(1)
