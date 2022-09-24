# This program performs a a simple scan for connected devices
# for a TCA9548A multiplexer hooked up to a SAMD51 Thing Plus dev board. 
import board
import adafruit_tca9548a

# Create I2C bus as normal
i2c = board.I2C()  # uses board.SCL and board.SDA

# Create the TCA9548A object and give it the I2C bus
tca = adafruit_tca9548a.TCA9548A(i2c)

for channel in range(8):
    if tca[channel].try_lock():
        print("Channel {}:".format(channel), end="")

        #print(type(tca[channel]))
        addresses = tca[channel].scan()
        print([hex(address) for address in addresses if address != 0x70])
        tca[channel].unlock()
