import cv2
import imutils
import time

screen_rect = None
screen_found = False
screen_settling = False
screen_good_timeout = time.time() + 1.0

def findScreen(frame):
    global screen_rect,screen_found
    global screen_good_timeout,screen_settling

    retVal = None
    
    # grab the raw NumPy array representing the image, then initialize the timestamp
    # and occupied/unoccupied text
    image = frame.array

    # initial crop
    image2 = image[80:480,0:640]

    if not screen_found:

        # make greyscale version
        gray_image = cv2.cvtColor(image2, cv2.COLOR_BGR2GRAY)

        # find lit area threshold
        ret,thresh = cv2.threshold(gray_image,63,255,cv2.THRESH_BINARY)

        # find the lit area contour
        #print cv2.findContours(thresh, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)
        contours, hierarchy = cv2.findContours(thresh, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)

        if len(contours) > 0:

            # extract the largest contour
            cnt = max(contours, key = cv2.contourArea)

            rect = cv2.minAreaRect(cnt)

            # and draw it
            cv2.drawContours(image2, [cnt], 0, (0,255,0), 3)

            w = int(rect[1][0])
            h = int(rect[1][1])

            x = int(rect[0][0]) - w / 2
            y = int(rect[0][1]) - h / 2

            r = rect[2]

            # also draw the bounding rectangle
            
            cv2.rectangle(image2,(x,y),(x+w,y+h),(255,0,0),2)

            #print x,y,w,h

            if x < 40 and y < 40 and w > 560 and h > 320 and r < 5 and r > -5:
                #contour is found that seems to be the screen
                
                #print 'Found screen at',x,y,w,h,r
                #screen_found = True
                screen_settling = True
                
                if screen_rect == None:
                    screen_rect = [x,y,w,h,r]
                else:
                    screen_rect = [min([screen_rect[0],x]),
                                   min([screen_rect[1],y]),
                                   max([screen_rect[2],w]),
                                   max([screen_rect[3],h]),r]
            else:
                screen_settling = False
                screen_good_timeout = time.time() + 1.0

            if screen_settling and time.time() > screen_good_timeout:
                screen_found = True
         
            # show the frame
            #cv2.imshow("Frame", image2)
            retVal = image2

    else:
        image3 = image2[screen_rect[1]:screen_rect[1]+screen_rect[3],
                        screen_rect[0]:screen_rect[0]+screen_rect[2]]
        image3 = imutils.rotate(image3, screen_rect[4])
        
        #cv2.imshow("Frame", image3)

        retVal = image3

    return screen_found,retVal
