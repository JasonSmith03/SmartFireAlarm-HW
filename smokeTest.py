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
from itertools import count
import matplotlib.pyplot as plt
import pandas as pd
from matplotlib.animation import FuncAnimation
#######################################Global variables################################################
#Threshold values deeming fire to be life threatning

temperatureThreshold = 33 #actual value: 57
smokeThreshold = 0.0002 #actual value: 3400
carbonMonoxideThreshold = 0.0009 #actual value: 35
LPGm = -0.47
LPGb = 1.31
SMOKEm = (math.log10(0.5/1.8))/(math.log10(10000/1000))
SMOKEb = math.log10(1.8) + SMOKEm * math.log10(1000)
COm = (math.log10(1.5/3.1))/(math.log10(10000/1000))
COb = math.log10(3.1) + COm * math.log10(1000)

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

#Plot sensor readings as a function of time 
xaxis_time = []
yaxis_temperature = 0]
yaxis_smoke = []
yaxis_co = []
index=count()
#######################################################################################################

# initializes MQ sensor and returns the the clean air resistance value.
def initMQSensor():
    '''
    Function to calibrate MQ2 sensor
    Authors: Jason Smith
             Bradley Rose
    '''
    mqSensor=0
    for i in range(0, 500):
        mqSensor += mq.value #calibration
    time.sleep(5)
    #calculate the sensing resistance in clean air
    rsAir = ((3.3 * 10) / mq.voltage) - 10 #3.3 volts and 10RL taken from the datasheet
    #calculate resistance in clean air from RS using air value
    cleanAirResistance = rsAir/9.9
    return cleanAirResistance

# Converts lmt84 reading from volts to temperature in degrees Celsius.
def getTemperature():
    '''
    This is method calculates the temperature of the LMT84 sensor in degrees Celcius using the formula derived from the LMT84 datasheet.
    '''
    milliVolts = (lmt84.voltage) * 1000
    temp_C = ((5.506 - math.sqrt(math.pow(-5.506, 2) + (4 * 0.00176 * (870.6 - milliVolts))))/(2 * -0.00176)) + 30 #LMT84 temp sensor transfer function
    temp_F = (temp_C * 9/5) + 32
    return temp_C, temp_F

#returns the ratio value used in all sensor readings below
def getRatio(cleanAirResistance):
    #RS calculation from detection
    rsGas = ((3.3 * 10) / mq.voltage) - 10
    #log of ratio to calculate ppm
    ratio = math.log10(rsGas/cleanAirResistance)
    return ratio

# returns the LPG sensor reading
def getLPG(cleanAirResistance):
    ratio = getRatio(cleanAirResistance)
    #LPG value in ppm
    LPGratio = (ratio - LPGb)/LPGm
    LPGppm = math.pow(10, LPGratio)
    LPGperc = LPGppm / 10000
    return LPGppm

# returns the smoke sensor reading
def getSmoke(cleanAirResistance):
    ratio = getRatio(cleanAirResistance)
    #Smoke value in ppm
    SMOKEratio = (ratio - SMOKEb)/SMOKEm
    SMOKEppm = math.pow(10, SMOKEratio)
    SMOKEperc = SMOKEppm / 10000
    return SMOKEppm

# returns the Carbon Monoxide reading
def getCO(cleanAirResistance):
    ratio = getRatio(cleanAirResistance)
    #CO value in ppm
    COratio = (ratio - COb)/COm
    COppm = math.pow(10, COratio)
    COperc = COppm / 10000
    return COppm

# check sensor readings against threshold values
def dangerous(temp_C, smokeReading, COreading):
    if (temp_C >= temperatureThreshold or smokeReading >= smokeThreshold or COreading >= carbonMonoxideThreshold):
        return True
    return False

#send get request to google cloud functions to alert users of danger
def alertUsers():
    os.system('spd-say "Fire"')
    x = requests.get(gcfURL)
    #print(x.status_code)

def animate(i):
    #https://makersportal.com/blog/2018/8/14/real-time-graphing-in-python
    #https://learn.sparkfun.com/tutorials/graph-sensor-data-with-python-and-matplotlib/update-a-graph-in-real-time
    xaxis_time.append(next(index))

    tempC, tempF=getTemperature()
    yaxis_temperature.append(tempC)

    plt.plot(xaxis_time, yaxis_temperature)

    

def main():
    cleanAirResistance = initMQSensor()

    # tempFig, ax1 = plt.subplots()
    # gasFig, ax2 = plt2.subplots()
    
    # ax1.legend()
    # ax1.set_title('Temperature vs Time')
    # ax1.set_ylabel('Temperature(degrees Celsius)')
    # ax1.set_xlabel('Time(ms)')

    # ax2.legend()
    # ax1.set_title('Smoke, CO vs Time')
    # ax1.set_ylabel('Gas(ppm)')
    # ax1.set_xlabel('Time(ms)')

    ani = FuncAnimation(plt.gcf(), animate, interval=1000)
    plt.tight_layout()
    plt.show()
    
    while True:
        temp_C, temp_F = getTemperature()
        LPGreading = getLPG(cleanAirResistance)
        smokeReading = getSmoke(cleanAirResistance)
        COreading = getCO(cleanAirResistance)

        if (dangerous(temp_C, smokeReading, COreading)):
            alertUsers()        

        # Print out the value and delay a second before looping again.
        print("Temperature: {}C {}F".format(temp_C, temp_F))
        # print("LPG%: {}%, LPGppm: {}ppm".format(LPGperc, LPGppm))
        print("COppm: {}ppm, SMOKEppm: {}ppm, LPGppm: {}ppm".format(COreading, smokeReading, LPGreading))
        time.sleep(1.0)

if __name__ == '__main__':
    main()
