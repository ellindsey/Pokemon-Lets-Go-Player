import cv2
import imutils
import numpy as np
import pytesseract
from PIL import Image
import time
import math

prior_screen = None
average_motion = None
frames_processed_for_motion = 0
TrackedObjects = list()
tracking_start = time.time()

class TrackedObject(object):
    def __init__(self,x,y,w,h):
        self.lastSpottedTime = time.time()
        self.lastUpdateTime = time.time()
        self.spotted = False
        self.location = (x + w / 2, y + h / 2)
        self.confidence = 1
        self.speed = 0

        #print 'Created tracked object at',self.location

    def ExamineMovement(self,x,y,w,h):
        when = time.time()
        new_location = (x + w / 2, y + h / 2)

        dist = math.sqrt((self.location[0] - new_location[0]) * (self.location[0] - new_location[0]) +
                         (self.location[1] - new_location[1]) * (self.location[1] - new_location[1]))

        #print self.location,'examining',new_location,'dist',dist

        if dist < (((when - self.lastSpottedTime) * 100) + 50):
            self.spotted = True
            self.location = new_location
            if time.time() > (self.lastUpdateTime + 0.1):
                if when - self.lastSpottedTime > 0:
                    self.speed = self.speed * 0.9 + 0.1 * (dist / (when - self.lastSpottedTime))
                self.confidence += 1
                if self.confidence > 50:
                    self.confidence = 50
            #print 'True'
            self.lastUpdateTime = time.time()
            return True
        else:
            #print 'False'
            return False

    def tick(self):
        if self.lastSpottedTime < (time.time() - 1.0):
            #print 'Tracked object died at',self.location
            return None
        else:
            if self.spotted:            
                self.lastSpottedTime = time.time()
            self.spotted = False
            return self

def ResetMotionDetection():
    global prior_screen
    global average_motion
    global frames_processed_for_motion
    global TrackedObjects
    
    prior_screen = None
    average_motion = None
    frames_processed_for_motion = 0
    TrackedObjects = list()
    tracking_start = time.time()

def DetectMotion(frame):
    global prior_screen
    global average_motion
    global frames_processed_for_motion
    global TrackedObjects

    fh, fw, fc = frame.shape
    gray_image = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

    if prior_screen == None or gray_image.shape != prior_screen.shape:
        immediate_motion = gray_image
        frames_processed_for_motion = 0
        #print 'a'
    else:
        #print gray_image.shape,prior_screen.shape
        immediate_motion = cv2.absdiff(gray_image,prior_screen)
        
    prior_screen = gray_image

    if average_motion == None or average_motion.shape != immediate_motion.shape:
        average_motion = immediate_motion
        frames_processed_for_motion = 0
        #print 'b'
    else:
        average_motion = cv2.addWeighted(average_motion, 0.9, immediate_motion, 0.1, 0)

    frames_processed_for_motion += 1

    #print frames_processed_for_motion

    if average_motion.shape != immediate_motion.shape or frames_processed_for_motion < 20:
        return False,frame,[]
    else:
        new_motion = cv2.absdiff(average_motion,immediate_motion)
    
    kernel = np.ones((5,5),np.uint8)
    new_motion = cv2.erode(new_motion,kernel,iterations = 1)

    edges = cv2.Canny(new_motion, 15, 20)

    contours, hierarchy = cv2.findContours(edges, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)

    x = int(fw * 0.45)
    y = int(fh * 0.3)
    w = int(fw * 0.1)
    h = int(fh * 0.4)
    
    result = findContoursExcluding(contours,x,y,w,h)

    candidate_motions = list()

    if len(result) > 0:

        for cnt in result:

            if cv2.contourArea(cnt) > 10:
                
                x,y,w,h = cv2.boundingRect(cnt)
                cv2.rectangle(frame,(x,y),(x+w,y+h),(0,255,0),1)

                candidate_motions.append((x,y,w,h))

    index = 0

    done = False

    while not done:

        if index < len(TrackedObjects):

            thing = TrackedObjects[index]

            reamining_motions = list()
            
            for x,y,w,h in candidate_motions:
            
                if not thing.ExamineMovement(x,y,w,h):
                    reamining_motions.append((x,y,w,h))

            candidate_motions = reamining_motions

            index += 1

        if index == len(TrackedObjects) and len(candidate_motions) > 0:
            
            x,y,w,h = candidate_motions[0]

            TrackedObjects.append(TrackedObject(x,y,w,h))

        if index == len(TrackedObjects):
            done = True
        
    newTrackedObjects = list()

    movement_results = list()

    for thing in TrackedObjects:
        #print thing.confidence,thing.speed
        #if thing.confidence > 10 and thing.speed > 50:
        cv2.circle(frame, thing.location, thing.confidence + 10, (0,0,255))
        retval = thing.tick()

        if retval != None:
            newTrackedObjects.append(thing)
            
            if (time.time() - tracking_start) > 10.0:
                if thing.confidence > 10 and thing.speed > 50:
                    #print thing.location,thing.confidence,thing.speed
                    
                    relative_location = (thing.location[0] / (fw * 1.0),thing.location[1] / (fh * 1.0))
                    
                    movement_results.append((thing.confidence,relative_location))
            
    TrackedObjects = newTrackedObjects

    if len(movement_results) > 0:
        movement_results.sort()
        movement_results.reverse()
        return True,frame,[movement_results]
    else:
        return False,frame,[]
    

def auto_canny(image, sigma=0.33):
    # compute the median of the single channel pixel intensities
    v = np.median(image)
 
    # apply automatic Canny edge detection using the computed median
    lower = int(max(0, (1.0 - sigma) * v))
    upper = int(min(255, (1.0 + sigma) * v))
    edged = cv2.Canny(image, lower, upper)
 
    # return the edged image
    return edged

def findContoursExcluding(contours,x,y,w,h):
    results = list()

    for cnt in contours:
        rect = cv2.boundingRect(cnt)

        x2,y2,w2,h2 = rect

        if ((x + w) < x2) or (x > (x2 + w2)) or ((y + h) < y2) or (y > (y2 + h2)) :

            results.append(cnt)

    return results

def findContoursFilling(contours,x,y,w,h,size = 0.5):
    results = list()

    for cnt in contours:
        rect = cv2.boundingRect(cnt)

        x2,y2,w2,h2 = rect

        if (x < x2 and (x2 + w2) < (x + w) and w2 > (w*size) and
            y < y2 and (y2 + h2) < (y + h) and h2 > (h*size)):

            results.append(cnt)

    return results

text_in_box = ''
cursorFound = False

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
