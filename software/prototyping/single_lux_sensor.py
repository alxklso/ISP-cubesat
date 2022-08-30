# Code that reports  lux from detected light
# using the adafruit VEML7700 sensor.
# Sensor data is displayed in the console 
# and also written in a newly created text file.

import time
import board
import digitalio
import adafruit_veml7700

led = digitalio.DigitalInOut(board.LED)
led.switch_to_output()
i2c = board.I2C()  # uses board.SCL and board.SDA
veml7700 = adafruit_veml7700.VEML7700(i2c)

# try creating text file for writing lux data in
# new measurement for each line in txt file
try:
    with open('/lux_data.txt','w') as f:
        while True:
            print("Ambient light (SI lux):", veml7700.lux)
            f.write(str(veml7700.lux)+ '\n')
            f.flush()
            led.value = not led.value
            time.sleep(1)

# if OS error occurs
except OSError as e:
    print('There was an OSError')
