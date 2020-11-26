import os
import time
import busio
import digitalio
import board
import math
import adafruit_mcp3xxx.mcp3008 as MCP
from adafruit_mcp3xxx.analog_in import AnalogIn

# create the spi bus
spi = busio.SPI(clock=board.SCK, MISO=board.MISO, MOSI=board.MOSI)

# create the cs (chip select)
cs = digitalio.DigitalInOut(board.D22)

# create the mcp object
mcp = MCP.MCP3008(spi, cs)

# create an analog input channel on pin 0
lmt84 = AnalogIn(mcp, MCP.P0)

# Function to simplify the math of reading the temperature.
def tmp36_temperature_C(tempSensor):
    print('Raw ADC Value: ', lmt84.value)
    print('ADC Voltage: ' + str(lmt84.voltage) + 'V')
    millivolts = (lmt84.voltage) * 1000
    print("VOLTAGE: {}V".format(lmt84.voltage))
    print("MILLIVOLTAGE: {}mV".format(millivolts))
    tempC = ((5.506 - math.sqrt(math.pow(-5.506, 2) + (4 * 0.00176 * (870.6 - millivolts))))/(2 * -0.00176)) + 30 #LMT84 temp sensor transfer function
    return tempC


# Loop forever.
while True:
    # Read the temperature in Celsius.
    temp_C = tmp36_temperature_C(lmt84)
    # Convert to Fahrenheit.
    temp_F = (temp_C * 9/5) + 32
    # Print out the value and delay a second before looping again.
    print("Temperature: {}C {}F".format(temp_C, temp_F))
    time.sleep(1.0)