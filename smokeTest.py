import os
import time
import busio
import digitalio
import board
import math
import adafruit_mcp3xxx.mcp3008 as MCP
from adafruit_mcp3xxx.analog_in import AnalogIn
from picamera import PiCamera
from time import sleep

#Threshold values deeming fire to be life threatning
#Note that the values found below are test values based on current testing conditions as noted in the project report
TEMPERATURE_THRESHOLD = 30 #actual value: 57
SMOKE_THRESHOLD = 0.0002 #actual value: 3400
CARBON_MONOXIDE_THRESHOLD = 0.0009 #actual value: 35

# create the spi bus
spi = busio.SPI(clock=board.SCK, MISO=board.MISO, MOSI=board.MOSI)

# create the cs (chip select)
cs = digitalio.DigitalInOut(board.D22)

# create the mcp object
mcp = MCP.MCP3008(spi, cs)

# create an analog input channel on pin 0
lmt84 = AnalogIn(mcp, MCP.P0)
mq = AnalogIn(mcp, MCP.P1)

#create camera object
camera = PiCamera()

# Function to simplify the math of reading the temperature.
def lmt84_temperature_C(tempSensor):
    '''
    This is method calculates the temperature of the LMT84 sensor in degrees Celcius using the formula derived from the LMT84 datasheet.
    '''
    milliVolts = (lmt84.voltage) * 1000
    tempC = ((5.506 - math.sqrt(math.pow(-5.506, 2) + (4 * 0.00176 * (870.6 - milliVolts))))/(2 * -0.00176)) + 30 #LMT84 temp sensor transfer function
    return tempC

def calibration(mqSensor):
    '''
    This method calibrates the MQ2 sensor to get a sample of clean air during setup. 
    '''
    counter = 0
    for counter in range(0, 500):
        mqSensorCalibrated = mqSensor + mq.value
        counter = counter + 1
    return mqSensorCalibrated


mqSensor = 0 #variable to store sensor value
print("Calibrating...")
calibrationValue = calibration(mqSensor)
time.sleep(5.0)
#get the average value
mqAverageValue = calibrationValue / 500
#calculate the sensing resistance in clean air
#3.3 volts and 10RL taken from the datasheet
airResistance = (((3.3 * 10) / mq.voltage) - 10)/9.9

while True:
    # Read the temperature in Celsius.
    temp_C = lmt84_temperature_C(lmt84)
    # Convert to Fahrenheit.
    temp_F = (temp_C * 9/5) + 32
    
    # lpgM = (math.log10(0.27/0.8))/(math.log10(10000/1000))
    # lpgB = math.log10(0.8) + lpgM * math.log10(1000)
    
    LPGM = -0.47
    LPGB = 1.31
    
    SMOKE_M = (math.log10(0.5/1.8))/(math.log10(10000/1000))
    SMOKE_B = math.log10(1.8) + SMOKE_M * math.log10(1000)
    
    CARBON_MONOXIDE_M = (math.log10(1.5/3.1))/(math.log10(10000/1000))
    CARBON_MONOXIDE_B = math.log10(3.1) + CARBON_MONOXIDE_M * math.log10(1000)
    
    #digital value from detection
    mqValue = mq.value
    #Gas resistance calculation from detection
    gasResistance = ((3.3 * 10) / mq.voltage) - 10
    #gas to air ppm ratio using log10
    gasAirRatioPpm = math.log10(gasResistance/airResistance)
    
    #LPG value in ppm
    lpgRatio = (gasAirRatioPpm - LPGB)/LPGM
    lpgPpm = math.pow(10, lpgRatio)
    lpgPercentage = lpgPpm / 10000
    #Smoke value in ppm
    smokeRatio = (gasAirRatioPpm - SMOKE_B)/SMOKE_M
    smokePpm = math.pow(10, smokeRatio)
    smokePercentage = smokePpm / 10000
    #CarbonMonoxide value in ppm
    carbonMonoxideRatio = (gasAirRatioPpm - CARBON_MONOXIDE_B)/CARBON_MONOXIDE_M
    carbonMonoxidePpm = math.pow(10, carbonMonoxideRatio)
    carbonMonoxidePercentage = carbonMonoxidePpm / 10000

    #start camera once dangerous values are read
    if (temp_C >= TEMPERATURE_THRESHOLD or smokePpm >= SMOKE_THRESHOLD or carbonMonoxidePpm >= CARBON_MONOXIDE_THRESHOLD):
        camera.start_preview()
        camera.start_recording('/home/pi/SmartFire/VideoFiles/video.h264')
        #note this is currently for testing purposes, will need to define rule set for how long camera stays on and when it turns off
        sleep(10)
        camera.stop_recording()
        camera.stop_preview()
    
    # Print out the value and delay a second before looping again.
    print("Temperature: {}C {}F".format(temp_C, temp_F))
    # print("LPG%: {}%, LPGppm: {}ppm".format(LPGperc, LPGppm))
    print("COppm: {}ppm, smokePpm: {}ppm, lpgPpm: {}ppm".format(carbonMonoxidePpm, smokePpm, lpgPpm))
    print("CO%: {}%, SMOKE%: {}%, LPG%: {}%".format(carbonMonoxidePercentage, smokePercentage, lpgPercentage))
    print()
    print()
    time.sleep(1.0)
