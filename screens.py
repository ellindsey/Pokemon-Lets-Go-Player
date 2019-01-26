import cv2
import imutils
import time
import numpy as np
import argparse
import glob
import pytesseract
import os
from PIL import Image

import buttons
import servo

text_in_box = ''
cursorFound = False

def auto_canny(image, sigma=0.33):
    # compute the median of the single channel pixel intensities
    v = np.median(image)
 
    # apply automatic Canny edge detection using the computed median
    lower = int(max(0, (1.0 - sigma) * v))
    upper = int(min(255, (1.0 + sigma) * v))
    edged = cv2.Canny(image, lower, upper)
 
    # return the edged image
    return edged

def findContoursFilling(contours,x,y,w,h,size = 0.5):
    results = list()

    for cnt in contours:
        rect = cv2.boundingRect(cnt)

        x2,y2,w2,h2 = rect

        if (x < x2 and (x2 + w2) < (x + w) and w2 > (w*size) and
            y < y2 and (y2 + h2) < (y + h) and h2 > (h*size)):

            results.append(cnt)

    return results

def DetectTextBox(frame):
    global text_in_box
    global cursorFound
    
    fh, fw, fc = frame.shape
    gray_image = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    edges = auto_canny(gray_image,sigma = 0.5)
    contours, hierarchy = cv2.findContours(edges, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)

    x = int(fw * 0.178)
    y = int(fh * 0.766)
    w = int(fw * 0.650)
    h = int(fh * 0.226)

    result = findContoursFilling(contours,x,y,w,h,size = 0.8)
    
    if len(result) > 0:
        
        cv2.rectangle(frame,(x,y),(x+w,y+h),(0,255,255),2)

        cv2.drawContours(frame, result, 0, (0,255,0), 1)

        #look for a cursor

        x = int(fw * 0.765)
        y = int(fh * 0.88)
        w = int(fw * 0.043)
        h = int(fh * 0.088)
        
        result = findContoursFilling(contours,x,y,w,h,size = 0.3)

        if len(result) > 0:
            
            cv2.rectangle(frame,(x,y),(x+w,y+h),(255,0,0),2)

            cv2.drawContours(frame, result, 0, (255,0,255), 1)

            cursorFound = True

            if text_in_box == '':

                x = int(fw * 0.205)
                y = int(fh * 0.803)
                w = int(fw * 0.560)
                h = int(fh * 0.162)
                
                cv2.rectangle(frame,(x,y),(x+w,y+h),(0,0,0),1)

                #clip out the region with text

                textbox = gray_image[y:y+h,x:x+w]

                #scale it by 200%

                kernel = np.array([[-1,-1,-1], [-1,9,-1], [-1,-1,-1]])
                textbox = cv2.filter2D(textbox, -1, kernel)

                textbox = cv2.resize(textbox, (w * 2, h * 2), interpolation = cv2.INTER_LINEAR)

                #sharpen it
                
                th, textbox = cv2.threshold(textbox, 125, 255, cv2.THRESH_BINARY)

                #saving it to a file, mostly so I can check the intermediate stage

                filename = "temp.png"
                cv2.imwrite(filename, textbox)

                #Text recognition

                time_started = time.time()

                text_in_box = pytesseract.image_to_string(Image.open(filename))

                duration = time.time() - time_started
                
                print(text_in_box),"(%4.2fs)" % duration
        
        else:
            if cursorFound:
                text_in_box = ''
                
            cursorFound = False
            
        return True,frame,[cursorFound,text_in_box]
    else:
        text_in_box = ''
        return False,frame,[False,'']
                
def DetectMenu(frame):
    fh, fw, fc = frame.shape
    gray_image = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    edges = auto_canny(gray_image,sigma = 0.5)
    contours, hierarchy = cv2.findContours(edges, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)

    #frame = edges

    found_shapes = [0] * 5

    arrow_location = -1
    arrow_count = 0
    
    for i in range(5):
        x = int(fw * (i * 0.162 + 0.114))
        y = int(fh * 0.546)
        w = int(fw * 0.128)
        h = int(fh * 0.216)

        result = findContoursFilling(contours,x,y,w,h,size = 0.7)

        found_shapes[i] = len(result)

        if len(result) > 0:
            cv2.rectangle(frame,(x,y),(x+w,y+h),(0,255,255),2)

            cv2.drawContours(frame, result, 0, (0,255,0), 1)
                
        x = int(fw * (i * 0.162 + 0.092))
        y = int(fh * 0.610)
        w = int(fw * 0.053)
        h = int(fh * 0.091)
        
        result = findContoursFilling(contours,x,y,w,h,size = 0.3)

        found_shapes[i] += len(result)

        if len(result) > 0:
            cv2.rectangle(frame,(x,y),(x+w,y+h),(255,0,0),2)

            cv2.drawContours(frame, result, 0, (255,0,255), 1)

            arrow_location = i

            arrow_count += 1

    if all(map(lambda x:x>0,found_shapes)) and arrow_location > -1 and arrow_count == 1:
        
        return True,frame,[arrow_location]
    else:
        return False,frame,[-1]

class defaultScreen(object):
    def __init__(self):
        self.entryTime = time.time()
        self.last_press = None
        self.last_press_time = time.time()
        print 'Entering DefaultScreen'

    def tick(self,frame,goals):

        #look for text box
        
        textBoxfound,frame,retvals = DetectTextBox(frame)
        
        if (goals.needSave and
            time.time() > (self.entryTime + 5.0) and
            time.time() > (self.last_press_time + 0.5)):
            
            #enter menu screen if we have to
            
            buttons.pressX()
            self.last_press = 'X'
            self.last_press_time = time.time()
            return ExpectingMenuScreen(),frame
        elif (textBoxfound and retvals[0] and
            time.time() > (self.last_press_time + 0.5)):
            buttons.pressA()
            self.last_press = 'A'
            self.last_press_time = time.time()
            return self,frame
        else:
            return self,frame

class ExpectingMenuScreen(object):
    def __init__(self):
        self.entryTime = time.time()
        self.exitTime = time.time() + 2.0
        
        print 'Entering ExpectingMenuScreen'
        
    def tick(self,frame,goals):

        #look for menu

        menufound,frame,retvals = DetectMenu(frame)

        if menufound:
            return MenuScreen(),frame
        elif self.exitTime < time.time():
            return defaultScreen(),frame
        else:
            return self,frame 

class MenuScreen(object):
    def __init__(self):
        self.entryTime = time.time()
        self.exitTime = time.time() + 1.0
        
        print 'Entering MenuScreen'

        self.last_press = None
        self.last_press_time = time.time()
        
        self.selected_item = 2
        self.target_item = -1
        
    def tick(self,frame,goals):
        #look for menu

        menufound,frame,retval = DetectMenu(frame)

        if menufound:
            self.exitTime = time.time() + 1.0
            if retval[0] != -1:
                self.selected_item = retval[0]
                
            if goals.needSave: #do we need to save?
                self.target_item = 4

            #move the cursor if we have to

            if self.selected_item != -1 and self.target_item != -1:
                if time.time() > (self.last_press_time + 0.5):
                    if self.selected_item < self.target_item:
                        servo.pulse_right()
                        self.last_press_time = time.time()
                        self.last_press = 'R'
                    elif self.selected_item > self.target_item:
                        servo.pulse_left()
                        self.last_press_time = time.time()
                        self.last_press = 'L'
                    else:
                        buttons.pressA()
                        self.last_press_time = time.time()
                        self.last_press = 'A'
                        
            elif self.target_item == -1: #done in this screen?
                buttons.pressB()
                self.last_press_time = time.time()
                self.last_press = 'B'
                return defaultScreen(),frame

        if self.exitTime < time.time():
            if self.last_press == 'A':
                if self.selected_item == 0:
                    #menu 0 - pokedex
                    return defaultScreen(),frame #placeholder for pokedex screen
                elif self.selected_item == 1:
                    #menu 1 - bag
                    return defaultScreen(),frame #placeholder for bag screen
                elif self.selected_item == 2:
                    #menu 2 - party
                    return defaultScreen(),frame #placeholder for party screen
                elif self.selected_item == 3:
                    #menu 3 - communicate
                    return defaultScreen(),frame #placeholder for communicate screen
                elif self.selected_item == 4:
                    #menu 4 - save
                    return SavingScreen(),frame #save screen
                else:
                    return defaultScreen(),frame
            else:
                return defaultScreen(),frame
        else:
            return self,frame    

class SavingScreen(object):
    def __init__(self):
        print 'Entering SavingScreen'

    def tick(self,frame,goals):
        #hard-scripted blind sequence for now.
        
        time.sleep(1.0)
        buttons.pressA()
        time.sleep(5.0)
        buttons.pressB()
        goals.needSave = False
        
        return ExpectingMenuScreen(),frame #assume it worked
