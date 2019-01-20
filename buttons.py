from gpiozero import LED
import time

buttonY = LED(22)
buttonA = LED(23)
buttonB = LED(24)
buttonX = LED(25)

def pressA(duration = 0.25):
    buttonA.on()
    time.sleep(duration)
    buttonA.off()

def pressB(duration = 0.25):
    buttonB.on()
    time.sleep(duration)
    buttonB.off()

def pressX(duration = 0.25):
    buttonX.on()
    time.sleep(duration)
    buttonX.off()

def pressY(duration = 0.25):
    buttonY.on()
    time.sleep(duration)
    buttonY.off()

def test():
    pressA()
    time.sleep(0.25)
    pressB()
    time.sleep(0.25)
    pressX()
    time.sleep(0.25)
    pressY()
    time.sleep(0.25)

#for i in range(10):
#    test()
    

