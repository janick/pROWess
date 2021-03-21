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
import time


def now():
    return int(time.time())

#
# Frame with a set of widgets that displays the main workout numbers
#
class NumbersFrame(tk.Frame):
    def __init__(self, parent, **kwargs):
        super().__init__(parent, kwargs)

        self.WorkoutTime = tk.Label(master=self, text="--:--", font=('Arial', 40), width=7)
        self.StrokeRate  = tk.Label(master=self, text="--", font=('Arial bold', 50), width=3)
        self.SplitTime   = tk.Label(master=self, text=" -:--", font=('Arial bold', 50), width=7)
        self.Distance    = tk.Label(master=self, text="---- m", font=('Arial', 40), width=7)
        self.HeartRate   = tk.Label(master=self, text="---", font=('Arial bold', 60), fg='red', width=3)
        self.Status      = tk.Label(master=self, text="Disconnected", font=('Arial', 20))


        self.TimeLabel = tk.Label(master=self, text="Time:", anchor="e", font=('Arial', 25), width=6)
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


class MainDisplay(tk.Tk):

    def __init__(self, height, width):
        super().__init__()
        geo = str(width) + "x" + str(height)
        self.geometry(geo)

        # Main Layout
        self.winfo_toplevel().title("pROWess")
        topHalfFrame    = tk.Frame(master=self, relief=tk.RIDGE, borderwidth=5, height=int(height*2/3))
        bottomHalfFrame = tk.Frame(master=self, relief=tk.RIDGE, borderwidth=5, height=int(height*1/3))
        self.columnconfigure(0, weight=1)
        self.rowconfigure(1, weight=1)
        topHalfFrame.grid(   row=0, column=0, sticky=tk.N+tk.S+tk.E+tk.W)
        bottomHalfFrame.grid(row=1, column=0, sticky=tk.N+tk.S+tk.E+tk.W)
        self.update()

        # Bottom half layout
        bottomLeftFrame   = tk.Frame(master=bottomHalfFrame, borderwidth=1, relief=tk.GROOVE)
        bottomMiddleFrame = tk.Frame(master=bottomHalfFrame, borderwidth=1, relief=tk.GROOVE)
        bottomRightFrame  = NumbersFrame(bottomHalfFrame, borderwidth=1, relief=tk.GROOVE)
        bottomHalfFrame.rowconfigure(0, weight=1)
        bottomHalfFrame.columnconfigure(0, weight=1)
        bottomHalfFrame.columnconfigure(1, weight=1)
        bottomLeftFrame.grid(  row=0, column=0, sticky=tk.N+tk.S+tk.E+tk.W)
        bottomMiddleFrame.grid(row=0, column=1, sticky=tk.N+tk.S+tk.E+tk.W)
        bottomRightFrame.grid( row=0, column=2, sticky=tk.N+tk.S)
        self.update()

        # Keep reference to the frames we need to update
        self.Numbers = bottomRightFrame
        self.startTime = None
        self.lastTime  = None
        self.distance  = 0
        self.heartBeatState = False

        self.distanceGoal = None
        self.durationGoal = None

        self.freeze = False

    #
    # Configure the next split
    #
    def configureSplit(self, duration, distance):
        self.durationGoal = duration
        if self.durationGoal == None:
            self.Numbers.TimeLabel.configure(text="Time:")
        else:
            self.Numbers.TimeLabel.configure(text="Left:")
            self.Numbers.WorkoutTime.configure(text=MMSS(self.durationGoal))
            
        self.distanceGoal = distance
        if self.distanceGoal == None:
            self.Numbers.DistanceLabel.configure(text="Dist:")
        else:
            self.Numbers.DistanceLabel.configure(text="Left:")
            self.Numbers.Distance.configure(text="{:4d} m".format(int(self.distanceGoal)))
    
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
        self.Numbers.Heart.configure(fg=color)


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

        splitDone = False;
        
        duration = nowT - self.startTime
        if self.durationGoal == None:
            self.Numbers.WorkoutTime.configure(text=MMSS(duration))
        else:
            left = self.durationGoal - duration
            if left < 0:
                left = 0
            self.Numbers.WorkoutTime.configure(text=MMSS(left))
            if left == 0:
                splitDone = True

        self.Numbers.SplitTime.configure(text=MMSS(500 / speedInMeterPerSec))

        self.distance += speedInMeterPerSec * (nowT - self.lastTime)
        if self.distanceGoal == None:
            self.Numbers.Distance.configure(text="{:4d} m".format(int(self.distance)))
        else:
            left = self.distanceGoal - self.distance
            if left < 0:
                left = 0
            self.Numbers.Distance.configure(text="{:4d} m".format(int(left)))
            if left == 0:
                splitDone = True

        self.lastTime = nowT
        return splitDone
        
        
    def updateStrokeRate(self, strokesPerMin):
        if self.freeze:
            return
        
        self.Numbers.StrokeRate.configure(text=str(strokesPerMin))

        
    def updateHeartBeat(self, beatsPerMin):
        if beatsPerMin == 255:
            return
        self.Numbers.HeartRate.configure(text=str(beatsPerMin))


    def updateStatus(self, text, color='black'):
        self.Numbers.Status.configure(text=text, fg=color)


#
# Format a timevalue (in seconds) into a MM:SS string
#
def MMSS(seconds):
        return "{:2d}:{:02d}".format(int(seconds/60), int(seconds)%60)
