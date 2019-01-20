# import the necessary packages
from picamera.array import PiRGBArray
from picamera import PiCamera
import time
import cv2
import imutils

import buttons
import servo
import screenGrab
import screens
import game

# initialize the camera and grab a reference to the raw camera capture
camera = PiCamera()
camera.resolution = (640, 480)
camera.framerate = 32
rawCapture = PiRGBArray(camera, size=camera.resolution)

saveindex = 0

goals = game.Goals()

goals.needSave = False
 
# allow the camera to warmup
time.sleep(0.1)

key = 0
lastKey = 0

activeScreen = screens.defaultScreen()
 
# capture frames from the camera
for frame in camera.capture_continuous(rawCapture, format="bgr", use_video_port=True):

    screen_found,image = screenGrab.findScreen(frame)

    if screen_found:
        activeScreen,image = activeScreen.tick(image,goals)

    if image != None:   
        cv2.imshow("Frame", image)
        key = cv2.waitKey(1) & 0xFF
    
    # clear the stream in preparation for the next frame
    rawCapture.truncate(0)

    if key != lastKey:

        if key == ord("q"): #quit
            break
        elif key == ord("s"): #save image
            if screen_found:
                cv2.imwrite( "/home/pi/images/img"+str(saveindex)+".jpg", image );	    
                saveindex += 1
        elif key == ord("a"):
            buttons.pressA()
        elif key == ord("b"):
            buttons.pressB()
        elif key == ord("x"):
            buttons.pressX()
        elif key == ord("y"):
            buttons.pressY()
        elif key == ord("r"):
            servo.pulse_right()
        elif key == ord("l"):
            servo.pulse_left()
        elif key == ord("u"):
            servo.pulse_up()
        elif key == ord("d"):
            servo.pulse_down()

    lastKey = key
