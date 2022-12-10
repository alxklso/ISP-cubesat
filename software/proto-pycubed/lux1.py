# Code that test the VEML7700 lux sensor, which is connected via I2C in the payload bay
from pycubed import cubesat
import time
import board
import busio
import adafruit_veml7700


# Declare and initialize i2c protocol using secondary SCL2 and SDA2 channels in PyCubed
# payload bay. Then set up lux sensor using i2c.
i2c2 = busio.I2C(board.SCL2, board.SDA2)
veml7700 = adafruit_veml7700.VEML7700(i2c2)

while True:
    print('Ambient light (SI lux)', veml7700.lux)
    time.sleep(1)
#print('worked') # Debugging purposes
