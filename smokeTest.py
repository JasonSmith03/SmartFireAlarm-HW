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
import matplotlib.pyplot as plt
import numpy as np
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
size = 100
x_vec = np.linspace(0,1,size+1)[0:-1]
y_vec = np.random.randn(len(x_vec))
y2_vec = np.random.randn(len(x_vec))
y3_vec = np.random.randn(len(x_vec))
line1 = []
line2 = []
line3 = []
plt.style.use('ggplot')
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

def live_plotter(x_vec,y1_data,line1,identifier='',pause_time=0.1):
    if line1==[]:
        # this is the call to matplotlib that allows dynamic plotting
        plt.ion()
        fig = plt.figure()
        ax = fig.add_subplot(111)
        # create a variable for the line so we can later update it
        line1, = ax.plot(x_vec,y1_data,'-o',alpha=0.8)        
        #update plot label/title
        plt.ylabel('Y Label')
        plt.title('Title: {}'.format(identifier))
        plt.show()
    
    # after the figure, axis, and line are created, we only need to update the y-data
    line1.set_ydata(y1_data)
    # adjust limits if new data goes beyond bounds
    if np.min(y1_data)<=line1.axes.get_ylim()[0] or np.max(y1_data)>=line1.axes.get_ylim()[1]:
        plt.ylim([np.min(y1_data)-np.std(y1_data),np.max(y1_data)+np.std(y1_data)])
    # this pauses the data so the figure/axis can catch up - the amount of pause can be altered above
    plt.pause(pause_time)
    
    # return line so we can update it again in the next iteration
    return line1

    

def main():
    cleanAirResistance = initMQSensor()
    
    while True:
        temp_C, temp_F = getTemperature()
        LPGreading = getLPG(cleanAirResistance)
        smokeReading = getSmoke(cleanAirResistance)
        COreading = getCO(cleanAirResistance)

        if (dangerous(temp_C, smokeReading, COreading)):
            alertUsers()   

        rand_val = np.random.randn(1)
    
        y_vec[-1] = rand_val
        line1 = live_plotter(x_vec,y_vec,line1)
        y_vec = np.append(y_vec[1:],0.0)

        y2_vec[-1] = rand_val
        line2 = live_plotter(x_vec,y2_vec,line2)
        y2_vec = np.append(y2_vec[1:],0.0)

        y3_vec[-1] = rand_val
        line3 = live_plotter(x_vec,y3_vec,line3)
        y3_vec = np.append(y3_vec[1:],0.0)     

        # Print out the value and delay a second before looping again.
        print("Temperature: {}C {}F".format(temp_C, temp_F))
        # print("LPG%: {}%, LPGppm: {}ppm".format(LPGperc, LPGppm))
        print("COppm: {}ppm, SMOKEppm: {}ppm, LPGppm: {}ppm".format(COreading, smokeReading, LPGreading))
        time.sleep(1.0)

if __name__ == '__main__':
    main()
