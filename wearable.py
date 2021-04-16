import time
import board
from digitalio import DigitalInOut, Direction

vibrating_motor = DigitalInOut(board.D1)    # initializing the vibrating motor to pin D1 of th emicroprocessor
vibrating_motor.direction = Direction.OUTPUT    # setting the direction of power to output from microcontroller

while True:

    loudVIB()

    time.sleep(3)

    FIREtoMorseVib()

    time.sleep(3)

def FIREtoMorseVib():   # Morse code rules: . = 1 time unit, - = 3 time units, space in between . and - = 1 time unit, space between letters = 3 time units

    # letter 'f' in morse code
    # dot
    vibrating_motor.value = True
    time.sleep(1)
    vibrating_motor.value = False

    time.sleep(1)

    #dot
    vibrating_motor.value = True
    time.sleep(1)
    vibrating_motor.value = False

    time.sleep(1)

    #dash
    vibrating_motor.value = True
    time.sleep(3)
    vibrating_motor.value = False

    time.sleep(1)

    #dot
    vibrating_motor.value = True
    time.sleep(1)
    vibrating_motor.value = False

    #time between letters
    time.sleep(3)

    # letter 'i' in morse code  
    #dot
    vibrating_motor.value = True
    time.sleep(1)
    vibrating_motor.value = False

    time.sleep(1)

    #dot
    vibrating_motor.value = True
    time.sleep(1)
    vibrating_motor.value = False

    #time between letters
    time.sleep(3)

    # letter 'r' in morse code
    #dot
    vibrating_motor.value = True
    time.sleep(1)
    vibrating_motor.value = False

    time.sleep(1)

    #dash
    vibrating_motor.value = True
    time.sleep(3)
    vibrating_motor.value = False

    time.sleep(1)

    #dot
    vibrating_motor.value = True
    time.sleep(2)
    vibrating_motor.value = False

    #time between letters
    time.sleep(3)

    #letter 'e' in morse code
    #dot
    vibrating_motor.value = True
    time.sleep(1)
    vibrating_motor.value = False

def loudVIB():

    vibrating_motor.value = True
    time.sleep(3)
    vibrating_motor.value = False

    time.sleep(2)

    vibrating_motor.value = True
    time.sleep(3)
    vibrating_motor.value = False

   