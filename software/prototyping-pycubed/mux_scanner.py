# This program performs a a simple scan for connected devices
# for a TCA9548A multiplexer hooked up to a SAMD51 Thing Plus dev board. 
import time 
import board
import busio
import adafruit_tca9548a

# Declare and initialize i2c protocol using secondary SCL2 and SDA2 channels in PyCubed
# payload bay. Then set up TCA9548A object and give it the I2C bus
i2c = busio.I2C(board.SCL2, board.SDA2)
tca = adafruit_tca9548a.TCA9548A(i2c)

for channel in range(8):
    if tca[channel].try_lock():
        print("Channel {}:".format(channel), end="")

        #print(type(tca[channel]))
        addresses = tca[channel].scan()
        print([hex(address) for address in addresses if address != 0x70])
        tca[channel].unlock()
