import time
import math
import buttons
import servo
import detect

class defaultScreen(object):
    def __init__(self):
        self.entryTime = time.time()
        self.last_press = None
        self.last_press_time = time.time()
        detect.ResetMotionDetection()
        print 'Entering DefaultScreen'

    def tick(self,frame,goals):

        #look for text box
        
        textBoxfound,frame,retvals = detect.DetectTextBox(frame)

        if textBoxfound:
            detect.ResetMotionDetection()
        
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
        elif not textBoxfound:
            motionfound,frame,retvals = detect.DetectMotion(frame)
            if motionfound:
                best_movement_found = retvals[0][0]
                if best_movement_found[0] > 10:
                    screen_position = best_movement_found[1]
                    relative_position = (screen_position[0] - 0.5, screen_position[1] - 0.5)

                    d = math.sqrt(relative_position[0] * relative_position[0] + 
                                  relative_position[1] * relative_position[1])

                    offset = (relative_position[0] / d,relative_position[1]/d)
                    print best_movement_found,offset

                    servo.set_joystick(offset[0],0 - offset[1])

                    time.sleep(d * 3.0)

                    servo.set_joystick(0,0)

                    detect.ResetMotionDetection()
                
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

        menufound,frame,retvals = detect.DetectMenu(frame)

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

        menufound,frame,retval = detect.DetectMenu(frame)

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
