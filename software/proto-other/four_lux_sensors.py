# Code for reading data from multiple lux sensors.
# This program assumes the use of four VEML7700 lux sensors
# and one adafruit TCS9548A multiplexer, combined with a
# SAMD51 Thing Plus dev board.
# The sensor data (lux (SI) per sensors) is displayed in the
# console for each sensor with a frequency of 1Hz.
import time
import board
import adafruit_veml7700 # lux sensor
import adafruit_tca9548a # multiplexer


# Create I2C bus
i2c = board.I2C()

# Create the TCA9548A object and give it the I2C bus
tca = adafruit_tca9548a.TCA9548A(i2c)

# Create each VEML7700 using the TCA9548A channel instead of the I2C object
lux1 = adafruit_veml7700.VEML7700(tca[0])   # TCA channel 0
lux2 = adafruit_veml7700.VEML7700(tca[1])   # TCA channel 1
lux3 = adafruit_veml7700.VEML7700(tca[2])   # TCA channel 2
lux4 = adafruit_veml7700.VEML7700(tca[3])   # TCA channel 3


# Function for printing sensor data to the console.
def print_sensor_data(lux1, lux2, lux3, lux4):
    while True:
        print('Sensor 1: ' + str(lux1.lux) + ' lx (SI)')
        print('Sensor 2: ' + str(lux2.lux) + '  lx (SI)')
        print('Sensor 3: ' + str(lux3.lux) + '  lx (SI)')
        print('Sensor 4: ' + str(lux4.lux) + ' lx (SI)\n')
        time.sleep(1)


# Print out lux (SI) for each sensor indefinitely
try:
    # If D5 is shorted with gnd, then the drive is in write-only
    # mode and data can be written to a text file. Sensor data is
    # also printed to the console.
    with open('/sensor_data.txt', 'w') as f:
        f.write(str(lux1.lux) + '\n')
        f.write(str(lux2.lux) + '\n')
        f.write(str(lux3.lux) + '\n')
        f.write(str(lux4.lux) + '\n')
        print_sensor_data(lux1, lux2, lux3, lux4)

# OSError exception
# Otherwise, an OSError exception occurs, which means the drive is
# in read-only mode. Sensor data will still print to the console.
except OSError as e:
    print('There was an OSError')
    print_sensor_data(lux1, lux2, lux3, lux4)
