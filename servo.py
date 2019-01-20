import Adafruit_PCA9685
import time
import math
pwm = Adafruit_PCA9685.PCA9685(0x40)

freq = 50
period = 1000.0 / freq
pwm.set_pwm_freq(freq)
#pwm.set_all_pwm(0,int((1.5 / period) * 4096))

servo_offsets = [0,0,0,0]

#print int((1.0 / period) * 4096)

def setServoAngle(n,angle):
    pulsetime = (angle + servo_offsets[n]) / 90.0 + 0.5

    pulsetime = min([2.25,pulsetime])
    pulsetime = max([0.75,pulsetime])

    #print pulsetime

    onwidth = int((pulsetime / period) * 4096)

    #print onwidth

    pwm.set_pwm(n,0,onwidth)

#zero all servos
    
#for i in range(4):
    #setServoAngle(i,105) #rest position
    #setServoAngle(i,90) #rest position
    
#90 is center
#less is towards joystick, maximum inward is 75
#more is away from joystick
#pulled away from joystick position is 105

#servo 0 is up-pushing
#servo 1 is left-pushing
#servo 2 is down-pushing
#servo 3 is right-pushing

def set_joystick(x,y):
    #x = x - 0.1
    y = y - 0.1
    
    if (x > 0.0): #right
        setServoAngle(1,105)
        setServoAngle(3,max([75,90 - int((x - 0.0)*15)]))
    elif (x < 0.0): #left
        setServoAngle(3,105)
        setServoAngle(1,max([75,90 - int((0.0 - x)*15)]))
    else:
        setServoAngle(1,100)
        setServoAngle(3,100)
        
    if (y < 0.0): #down
        setServoAngle(0,105)
        setServoAngle(2,max([75,90 - int((0.0 - y)*15)]))
    elif (y > 0.0): #up
        setServoAngle(2,105)
        setServoAngle(0,max([75,90 - int((y - 0.0)*15)]))
    else:
        setServoAngle(0,100)
        setServoAngle(2,100)

def release_joystick():
    for i in range(4):
        setServoAngle(i,100)

def pulse_right(duration = 0.25,distance = 1.0):
    set_joystick(distance,0.0)
    time.sleep(duration)
    set_joystick(0.0,0.0)
 
def pulse_left(duration = 0.25,distance = 1.0):
    set_joystick(0 - distance,0.0)
    time.sleep(duration)
    set_joystick(0.0,0.0)

def pulse_up(duration = 0.25,distance = 1.0):
    set_joystick(0.0,distance)
    time.sleep(duration)
    set_joystick(0.0,0.0)

def pulse_down(duration = 0.25,distance = 1.0):
    set_joystick(0.0,0 - distance)
    time.sleep(duration)
    set_joystick(0.0,0.0)
   

set_joystick(0.0,0.0)

def test_joystick():
    set_joystick(0.0,0.0)
    time.sleep(0.5)
    set_joystick(0.0,1.0)
    time.sleep(0.5)
    set_joystick(0.0,-1.0)
    time.sleep(0.5)
    set_joystick(0.0,0.0)
    time.sleep(0.5)
    set_joystick(1.0,0.0)
    time.sleep(0.5)
    set_joystick(-1.0,0.0)
    time.sleep(0.5)
    set_joystick(0.0,0.0)
    time.sleep(0.25)
    set_joystick(0.0,1.0)
    time.sleep(0.25)
    set_joystick(1.0,1.0)
    time.sleep(0.25)
    set_joystick(1.0,0.0)
    time.sleep(0.25)
    set_joystick(1.0,-1.0)
    time.sleep(0.25)
    set_joystick(0.0,-1.0)
    time.sleep(0.25)
    set_joystick(-1.0,-1.0)
    time.sleep(0.25)
    set_joystick(-1.0,0.0)
    time.sleep(0.25)
    set_joystick(-1.0,1.0)
    time.sleep(0.25)
    set_joystick(0.0,1.0)
    time.sleep(0.25)
    set_joystick(0.0,0.0)
    
        

