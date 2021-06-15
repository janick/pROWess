#
# Copyright 2021  Janick Bergeron <janick@bergeron.com>
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#


import tkinter as tk
import tkinter.ttk
import time

import User

def now():
    return int(time.time())

#
# Frame with a set of widgets that displays the main workout numbers
#
class NumbersFrame(tk.Frame):
    def __init__(self, parent, **kwargs):
        super().__init__(parent, kwargs)

        self.grid_propagate(0)
        self.pack_propagate(0)

        self.WorkoutTime = tk.Label(master=self, text="--:--", font=('Arial', 40), width=5)
        self.StrokeRate  = tk.Label(master=self, text="--", font=('Arial bold', 50), width=2)
        self.SplitTime   = tk.Label(master=self, text=" -:--", font=('Arial bold', 50), width=5)
        self.Distance    = tk.Label(master=self, text="---- m", font=('Arial', 40), width=7)
        self.HeartRate   = tk.Label(master=self, text="---", font=('Arial bold', 60), fg='red', width=3)
        self.Status      = tk.Label(master=self, text="Disconnected", font=('Arial', 20))


        self.TimeLabel = tk.Label(master=self, text="Time:", anchor="e", font=('Arial', 25), width=5)
        self.TimeLabel.grid(row=0, column=0, sticky=tk.N+tk.S+tk.E+tk.W)
        self.WorkoutTime.grid(row=0, column=1, sticky=tk.N+tk.S+tk.E+tk.W)
        self.StrokeRate.grid( row=0, column=2, sticky=tk.N+tk.S+tk.E+tk.W)
        tk.Label(master=self, text="s/m", anchor="w", font=('Arial', 20)).grid(row=0, column=3, sticky=tk.N+tk.S+tk.E+tk.W)
        tk.Label(master=self, text="Split:", anchor="e", font=('Arial', 25)).grid(row=1, column=0, sticky=tk.N+tk.S+tk.E+tk.W)
        self.SplitTime.grid(  row=1, column=1, sticky=tk.N+tk.S+tk.E+tk.W)
        tk.Label(master=self, text="/500 m", anchor="w", font=('Arial', 25)).grid(row=1, column=2, columnspan=2, sticky=tk.N+tk.S+tk.E+tk.W)
        self.DistanceLabel = tk.Label(master=self, text="Dist:", anchor="e", font=('Arial', 25))
        self.DistanceLabel.grid(row=2, column=0, sticky=tk.N+tk.S+tk.E+tk.W)
        self.Distance.grid(   row=2, column=1, sticky=tk.N+tk.S+tk.E+tk.W)
        self.HeartRate.grid(  row=2, column=2, sticky=tk.N+tk.S+tk.E+tk.W)
        self.Heart = tk.Label(master=self, text="♥", anchor="w", font=('Arial bold', 60), fg='red')
        self.Heart.grid(row=2, column=3, sticky=tk.N+tk.S+tk.E+tk.W)
        self.Status.grid(row=3, column=0, columnspan=4, sticky=tk.N+tk.S+tk.E+tk.W)


class Progress(tk.Frame):
    def __init__(self, name, parent, **kwargs):
        super().__init__(parent, kwargs)

        self.name = "ProgressBar" + name
        self.style = tk.ttk.Style(self)
        self.style.configure(self.name, font=('Arial bold', 14), foreground='black')
        self.style.configure(self.name, background='#5ca3e0', foreground='#031e36')
        self.style.layout(self.name,
                          [(self.name + '.trough',
                            {'children': [(self.name + '.pbar', {'side': 'left', 'sticky': 'nsew'}),
                                          (self.name + '.label', {'sticky': ''})],
                             'sticky': 'nsew'})])

        self.bar = tk.ttk.Progressbar(self, orient=tk.HORIZONTAL, mode='determinate', style=self.name, length=User.screen['X']-16)

        self.columnconfigure(0, weight=1)
        self.rowconfigure(0, weight=1)
        self.bar.grid(row=0, column=0, sticky=tk.N+tk.S+tk.E+tk.W)
        self.updatePercent(50)

    def updatePercent(self, percent):
        if percent > 0:
            self.style.configure(self.name, text="{0} %".format(percent))
        else:
            self.style.configure(self.name, text="     ")
        self.bar['value'] = percent
        

class MainDisplay(tk.Tk):

    def __init__(self, width, height):
        super().__init__()
        geo = str(width) + "x" + str(height)
        self.geometry(geo)

        # Main Layout
        self.winfo_toplevel().title("pROWess")
        topFrame    = tk.Frame(master=self, relief=tk.GROOVE, borderwidth=0, height=height-200)
        bottomFrame = tk.Frame(master=self, relief=tk.RIDGE,  borderwidth=5, height=200)
        self.columnconfigure(0, weight=1)
        self.rowconfigure(0, weight=1)
        self.rowconfigure(1, weight=1)
        topFrame.grid(   row=0, column=0, sticky=tk.N+tk.S+tk.E+tk.W)
        bottomFrame.grid(row=1, column=0, sticky=tk.N+tk.S+tk.E+tk.W)

        topFrame.grid_propagate(0)
        bottomFrame.grid_propagate(0)

        # Top frame layout
        topLeftFrame   = tk.Frame(master=topFrame, relief=tk.RIDGE,  borderwidth=5)
        topMiddleFrame = tk.Frame(master=topFrame, relief=tk.RIDGE,  borderwidth=5)
        topRightFrame  = tk.Frame(master=topFrame, relief=tk.RIDGE,  borderwidth=5)
        topFrame.rowconfigure(0, weight=1)
        topFrame.columnconfigure(0, weight=1)
        topFrame.columnconfigure(1, weight=1)
        topFrame.columnconfigure(2, weight=1)
        topLeftFrame.grid(  row=0, column=0, sticky=tk.N+tk.S+tk.E+tk.W)
        topMiddleFrame.grid(row=0, column=1, sticky=tk.N+tk.S+tk.E+tk.W)
        topRightFrame.grid( row=0, column=2, sticky=tk.N+tk.S+tk.E+tk.W)

        topLeftFrame.grid_propagate(0)
        topMiddleFrame.grid_propagate(0)
        topRightFrame.grid_propagate(0)

        # Top-right frame layout
        topTopRightFrame    = tk.Frame(master=topRightFrame, relief=tk.GROOVE, borderwidth=5)
        bottomTopRightFrame = NumbersFrame(topRightFrame,    relief=tk.GROOVE, borderwidth=5)
        topRightFrame.columnconfigure(0, weight=1)
        topRightFrame.rowconfigure(0, weight=2)
        topRightFrame.rowconfigure(1, weight=1)
        topTopRightFrame.grid(   row=0, column=0, sticky=tk.N+tk.S+tk.E+tk.W)
        bottomTopRightFrame.grid(row=1, column=0, sticky=tk.N+tk.S+tk.E+tk.W)

        topTopRightFrame.grid_propagate(0)
        bottomTopRightFrame.grid_propagate(0)

        # Bottom frame layout
        topBottomFrame     = tk.Frame(master=bottomFrame, relief=tk.RIDGE, borderwidth=0)
        self.splitProgress = Progress("splitBar", bottomFrame,        relief=tk.RIDGE, borderwidth=1)
        tickMarks          = tk.Canvas(bottomFrame, bg="red", height=20);
        self.progress      = Progress("workoutBar", bottomFrame,        relief=tk.RIDGE, borderwidth=1)
        bottomBottomFrame  = tk.Frame(master=bottomFrame, relief=tk.RIDGE, borderwidth=0)
        bottomFrame.columnconfigure(0, weight=1)
        bottomFrame.rowconfigure(0, weight=1)
        bottomFrame.rowconfigure(1, weight=10)
        bottomFrame.rowconfigure(2, weight=1)
        bottomFrame.rowconfigure(3, weight=10)
        bottomFrame.rowconfigure(4, weight=1)
        topBottomFrame.grid(    row=0, column=0, sticky=tk.N+tk.S+tk.E+tk.W)
        self.splitProgress.grid(row=1, column=0, sticky=tk.N+tk.S+tk.E+tk.W)
        tickMarks.grid(         row=2, column=0, sticky=tk.N+tk.S+tk.E+tk.W)
        self.progress.grid(     row=3, column=0, sticky=tk.N+tk.S+tk.E+tk.W)
        bottomBottomFrame.grid( row=4, column=0, sticky=tk.N+tk.S+tk.E+tk.W)

        topBottomFrame.grid_propagate(0)
        self.splitProgress.grid_propagate(1)
        self.progress.grid_propagate(1)
        bottomBottomFrame.grid_propagate(0)

        self.update()
        
        # Keep reference to the frames we need to update
        self.numbers = bottomTopRightFrame
        self.startTime = None
        self.lastTime  = None
        self.distance  = 0
        self.heartBeatState = False

        self.distanceGoal = None
        self.durationGoal = None
        self.durationAccum = 0;
        self.distanceAccum = 0;
        self.distanceEndGoal = None
        self.durationEndGoal = None

        self.freeze = False


    #
    # Configure overall workout for progress bar
    #
    def configureEndGoal(self, duration, distance):
        self.durationAccum = 0;
        self.durationEndGoal = duration
        if self.durationEndGoal == None:
            self.numbers.TimeLabel.configure(text="Time:")
        else:
            self.durationEndGoal *= User.secsInOneMin
            self.numbers.TimeLabel.configure(text="Left:")
            self.numbers.WorkoutTime.configure(text=MMSS(self.durationEndGoal))

        self.distanceAccum = 0;
        if self.distanceEndGoal == None:
            self.numbers.DistanceLabel.configure(text="Dist:")
        else:
            self.distanceEndGoal = distance * User.metersInOneKm / 1000
            self.numbers.DistanceLabel.configure(text="Left:")
            self.numbers.Distance.configure(text="{:4d} m".format(int(self.distanceEndGoal)))
            
        
    #
    # Configure the next phase
    #
    def configurePhase(self, duration, distance):
        self.durationGoal = duration
        if self.durationGoal == None:
            self.numbers.TimeLabel.configure(text="Time:")
        else:
            self.durationGoal *= User.secsInOneMin
            self.numbers.TimeLabel.configure(text="Left:")
            self.numbers.WorkoutTime.configure(text=MMSS(self.durationGoal))

        if self.distanceGoal == None:
            self.numbers.DistanceLabel.configure(text="Dist:")
        else:
            self.distanceGoal = distance * User.metersInOneKm / 1000
            self.numbers.DistanceLabel.configure(text="Left:")
            self.numbers.Distance.configure(text="{:4d} m".format(int(self.distanceGoal)))
        
    
    #
    # Start/stop workout display
    #
    def start(self, nowT = None):
        if nowT is None:
            nowT = now()
            
        self.startTime = nowT
        self.lastTime  = nowT
        self.distance  = 0
        self.updateStatus("")

        self.freeze = False


    def heartBeat(self):
        self.heartBeatState = not self.heartBeatState
        color = 'red'
        if self.heartBeatState:
            color = 'black'
        self.numbers.Heart.configure(fg=color)


    def pause(self):
        self.lastTime  = now()
        self.updateStatus("PAUSED", 'red')
        self.freeze = True


    def resume(self):
        nowT = now()
        self.startTime += nowT - self.lastTime
        self.lastTime  = nowT
        self.updateStatus("")

        self.freeze = False


    def stop(self):
        self.pause()
        self.distance = 0
        self.distanceGoal = None
        self.durationGoal = None
        self.updateStatus("Done!")

    #
    # Update the data the display is tracking
    # Return True is the current split is finished
    #
    def updateSpeed(self, speedInMeterPerSec):
        if self.freeze:
            return False
        
        nowT = now()

        if speedInMeterPerSec == 0:
            return False

        if self.startTime is None:
            self.start(nowT)

        phaseDone = False;
        
        duration = nowT - self.startTime
        self.durationAccum += nowT - self.lastTime
        if self.durationGoal == None:
            self.numbers.WorkoutTime.configure(text=MMSS(duration))
        else:
            left = self.durationGoal - duration
            if left < 0:
                left = 0
            self.numbers.WorkoutTime.configure(text=MMSS(left))
            if left == 0:
                phaseDone = True
            if self.durationEndGoal != None and self.durationAccum <= self.durationEndGoal:
                self.progress.updatePercent(int(self.durationAccum * 100 / self.durationEndGoal))

        self.numbers.SplitTime.configure(text=MMSS(500 / speedInMeterPerSec))

        dist = speedInMeterPerSec * (nowT - self.lastTime)
        self.distance += dist
        self.distanceAccum += dist
        if self.distanceGoal == None:
            self.numbers.Distance.configure(text="{:4d} m".format(int(self.distance)))
        else:
            left = self.distanceGoal - self.distance
            if left < 0:
                left = 0
            self.numbers.Distance.configure(text="{:4d} m".format(int(left)))
            if left == 0:
                phaseDone = True
            if self.distanceEndGoal != None and self.distanceAccum <= self.distanceEndGoal:
                self.progress.updatePercent(int(self.distanceAccum * 100 / self.distanceEndGoal))

        self.lastTime = nowT

        return phaseDone
        
        
    def updateStrokeRate(self, strokesPerMin):
        if self.freeze:
            return
        
        self.numbers.StrokeRate.configure(text=str(strokesPerMin))

        
    def updateHeartBeat(self, beatsPerMin):
        if beatsPerMin == 255:
            return
        self.numbers.HeartRate.configure(text=str(beatsPerMin))


    def updateStatus(self, text, color='black'):
        self.numbers.Status.configure(text=text, fg=color)


#
# Format a timevalue (in seconds) into a MM:SS string
#
def MMSS(seconds):
        return "{:2d}:{:02d}".format(int(seconds/60), int(seconds)%60)
