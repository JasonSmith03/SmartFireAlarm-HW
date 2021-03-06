import os
import time
import busio
import digitalio
import board
import math
import requests
import adafruit_mcp3xxx.mcp3008 as MCP
from adafruit_mcp3xxx.analog_in import AnalogIn
from time import sleep


#######################################Global variables################################################
#Threshold values deeming fire to be life threatning

temperatureThreshold = 33 #actual value: 57
smokeThreshold = 0.0002 #actual value: 3400
carbonMonoxideThreshold = 0.0009 #actual value: 35

# create the spi bus
spi = busio.SPI(clock=board.SCK, MISO=board.MISO, MOSI=board.MOSI)

# create the cs (chip select)
cs = digitalio.DigitalInOut(board.D22)

# create the mcp object
mcp = MCP.MCP3008(spi, cs)

# create an analog input channel on pin 0
lmt84 = AnalogIn(mcp, MCP.P0)
mq = AnalogIn(mcp, MCP.P1)

#google cloud functions server endpoint designated to device ID
gcfURL = 'https://us-central1-smartfire-3e198.cloudfunctions.net/alarm?deviceId=10000000630c3886'
#######################################################################################################

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
    Function to calibrate MQ2 sensor
    Authors: Jason Smith
             Bradley Rose
    '''
    i = 0
    for i in range(0, 500):
        mqSensor = mqSensor + mq.value
        i = i + 1
    return mqSensor

def main():
    mqSensor = 0 #variable to store sensor value
    print("Calibrating...")
    
    calibrateVal = calibration(mqSensor)
    time.sleep(5.0)
    #get the average value
    mqAvgVal = calibrateVal / 500
    #calculate the sensing resistance in clean air
    #3.3 volts and 10RL taken from the datasheet
    rsAir = ((3.3 * 10) / mq.voltage) - 10
    #calculate resistance in clean air from RS using air value
    r0 = rsAir/9.9
    # Loop forever.

    while True:
        # Read the temperature in Celsius.
        temp_C = lmt84_temperature_C(lmt84)
        # Convert to Fahrenheit.
        temp_F = (temp_C * 9/5) + 32
        
    #     LPGm = (math.log10(0.27/0.8))/(math.log10(10000/1000))
    #     LPGb = math.log10(0.8) + LPGm * math.log10(1000)
        
        LPGm = -0.47
        LPGb = 1.31
        
        SMOKEm = (math.log10(0.5/1.8))/(math.log10(10000/1000))
        SMOKEb = math.log10(1.8) + SMOKEm * math.log10(1000)
        
        COm = (math.log10(1.5/3.1))/(math.log10(10000/1000))
        COb = math.log10(3.1) + COm * math.log10(1000)
        
        #digital value from detection
        mqValue = mq.value
        #RS calculation from detection
        rsGas = ((3.3 * 10) / mq.voltage) - 10
        #ratio from detection
        ratio1 = rsGas/r0
        #log of ratio to calculate ppm
        ratio = math.log10(ratio1)
        
        #LPG value in ppm
        LPGratio = (ratio - LPGb)/LPGm
        LPGppm = math.pow(10, LPGratio)
        LPGperc = LPGppm / 10000
        #Smoke value in ppm
        SMOKEratio = (ratio - SMOKEb)/SMOKEm
        SMOKEppm = math.pow(10, SMOKEratio)
        SMOKEperc = SMOKEppm / 10000
        #CO value in ppm
        COratio = (ratio - COb)/COm
        COppm = math.pow(10, COratio)
        COperc = COppm / 10000

        #send get request to google cloud functions and activate fire alarm
        if (temp_C >= temperatureThreshold or SMOKEppm >= smokeThreshold or COppm >= carbonMonoxideThreshold):
            os.system('spd-say "Fire"')
            x = requests.get(gcfURL)
            #print(x.status_code)

        # Print out the value and delay a second before looping again.
        print("Temperature: {}C {}F".format(temp_C, temp_F))
        # print("LPG%: {}%, LPGppm: {}ppm".format(LPGperc, LPGppm))
        print("COppm: {}ppm, SMOKEppm: {}ppm, LPGppm: {}ppm".format(COppm, SMOKEppm, LPGppm))
        print("CO%: {}%, SMOKE%: {}%, LPG%: {}%".format(COperc, SMOKEperc, LPGperc))
        print()
        print()
        time.sleep(1.0)

if __name__ == '__main__':
    main()
