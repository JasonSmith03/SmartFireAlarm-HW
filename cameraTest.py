from picamera import PiCamera
from time import sleep

camera = PiCamera()

camera.start_preview()
camera.start_recording('/home/pi/Desktop/video.h264') #change directory
sleep(5)
camera.stop_recording()
camera.stop_preview()


#https://projects.raspberrypi.org/en/projects/getting-started-with-picamera/6