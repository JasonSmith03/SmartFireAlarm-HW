import os
import time
import busio
import digitalio
import board
import math
import requests
import datetime as dt
import adafruit_mcp3xxx.mcp3008 as MCP
from adafruit_mcp3xxx.analog_in import AnalogIn
import matplotlib.pyplot as plt
import matplotlib.animation as animation
import numpy as np
#######################################Global variables################################################
#Threshold values deeming fire to be life threatning

temperatureThreshold = 35 #actual value: 57
smokeThreshold = 0.0002 #actual value: 3400
carbonMonoxideThreshold = 0.0009 #actual value: 35
LPGm = -0.47
LPGb = 1.31
SMOKEm = (math.log10(0.5/1.8))/(math.log10(10000/1000))
SMOKEb = math.log10(1.8) + SMOKEm * math.log10(1000)
COm = (math.log10(1.5/3.1))/(math.log10(10000/1000))
COb = math.log10(3.1) + COm * math.log10(1000)
cleanAirResistance = 1

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

#Graphing Data
fig = plt.figure()
temp_ax = fig.add_subplot(3, 1, 1)
smoke_ax = fig.add_subplot(3, 1, 2)
co_ax = fig.add_subplot(3, 1, 3)

xs = []
temp_ys = []
smoke_ys = []
co_ys = []
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

# Converts lmt84 reading from volts to temperature in degrees Celsius.
def getTemperature():
    '''
    This is method calculates the temperature of the LMT84 sensor in degrees Celcius using the formula derived from the LMT84 datasheet.
    '''
    milliVolts = (lmt84.voltage) * 1000
    temp_C = ((5.506 - math.sqrt(math.pow(-5.506, 2) + (4 * 0.00176 * (870.6 - milliVolts))))/(2 * -0.00176)) + 30 #LMT84 temp sensor transfer function
    temp_F = (temp_C * 9/5) + 32
    if (temp_C >= temperatureThreshold):
        alertUsers()
    print("Temperature: {}C {}F".format(temp_C, temp_F))
    return temp_C

#returns the ratio value used in all sensor readings below
def getRatio():
    #RS calculation from detection
    rsGas = ((3.3 * 10) / mq.voltage) - 10
    #log of ratio to calculate ppm
    ratio = math.log10(rsGas/cleanAirResistance)
    return ratio

# returns the LPG sensor reading
def getLPG():
    ratio = getRatio()
    #LPG value in ppm
    LPGratio = (ratio - LPGb)/LPGm
    LPGppm = math.pow(10, LPGratio)
    LPGperc = LPGppm / 10000
    return LPGppm

# returns the smoke sensor reading
def getSmoke():
    ratio = getRatio()
    #Smoke value in ppm
    SMOKEratio = (ratio - SMOKEb)/SMOKEm
    SMOKEppm = math.pow(10, SMOKEratio)
    SMOKEperc = SMOKEppm / 10000
    if(SMOKEppm >= smokeThreshold):
        alertUsers()
    print("SMOKEppm: {}ppm".format(SMOKEppm))
    return SMOKEppm

# returns the Carbon Monoxide reading
def getCO():
    ratio = getRatio()
    #CO value in ppm
    COratio = (ratio - COb)/COm
    COppm = math.pow(10, COratio)
    COperc = COppm / 10000
    if(COppm >= carbonMonoxideThreshold):
        alertUsers()
    print("COppm: {}ppm \n".format(COppm))
    return COppm

#send get request to google cloud functions to alert users of danger
def alertUsers():
    os.system('spd-say "Fire"')
    x = requests.get(gcfURL)
    #print(x.status_code)

# This function is called periodically from FuncAnimation
def animate(i, xs, temp_ys, smoke_ys, co_ys):
# https://learn.sparkfun.com/tutorials/graph-sensor-data-with-python-and-matplotlib/update-a-graph-in-real-time

    # Add x and y to lists
    localtime = dt.datetime.now().strftime('%H:%M:%S.')
    xs.append(localtime)
    temp_ys.append(getTemperature())
    smoke_ys.append(getSmoke())
    co_ys.append(getCO())


    # Limit x and y lists to 20 items
    xs = xs[-20:]
    temp_ys = temp_ys[-20:]
    smoke_ys = smoke_ys[-20:]
    co_ys = co_ys[-20:]
    
    
    
    # Draw x and y lists
    temp_ax.clear()
    temp_ax.plot(xs, temp_ys, color='red')
    temp_ax.axes.xaxis.set_visible(False)
    temp_ax.set_title('Temperature vs Time')
    temp_ax.set_ylabel('Temperature (deg C)')

    
    smoke_ax.clear()
    smoke_ax.plot(xs, smoke_ys)
    smoke_ax.axes.xaxis.set_visible(False)
    smoke_ax.set_title('Smoke vs Time')
    smoke_ax.set_ylabel('Smoke (ppm)')

    co_ax.clear()
    co_ax.plot(xs, co_ys, color='green')
    plt.xticks(rotation=45, ha='right')
    plt.subplots_adjust(bottom=0.30)
    co_ax.set_title('CO vs Time')
    co_ax.set_xlabel('Time (H:M:S)')
    co_ax.set_ylabel('CO (ppm)')
    
    fig.tight_layout(pad=3.0)
    
def main():
    initMQSensor()
    
    ani = animation.FuncAnimation(fig, animate, fargs=(xs,temp_ys,smoke_ys,co_ys), interval=1000)
    plt.show()
    
    

if __name__ == '__main__':
    main()
