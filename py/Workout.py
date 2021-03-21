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

import time


def now():
    return int(time.time())


class State:
    STARTED = 1
    PAUSED  = 2
    RESUMED = 3
    STOPPED = 4

    #
    # Idle -> Working out -> pause -> working out -> pause -> Ended
    #   0          1           2          1            2       3
    
    def __init__(self):
        self.state = 0
        self.when  = now()
        # You have 5 mins secs to resume a work-out
        self.maxPause = 5*60

    def reset(self):
        self.state = 0
        self.when  = now()

    def abort(self):
        self.state = 3
        self.when  = now()

    def isIdle(self):
        return self.state == 0

    def isRunning(self):
        return self.state == 1

    def isPaused(self):
        return self.state == 2

    def isEnded(self):
        return self.state == 3

    def hasBeenFor(self):
        return now() - self.when

    # Return None or state change
    def update(self, speed):
        if self.isEnded():
            return State.STOPPED
            
        if speed == 0:
            if self.isRunning():
                self.state = 2;
                self.when  = now()
                return State.PAUSED

            if self.isPaused():
                if self.hasBeenFor() >= self.maxPause:
                    self.state = 3;
                    self.when  = now()
                    return State.STOPPED
                    
            return None

        # Speed is > 0
        if self.isIdle():
            self.state = 1;
            self.when  = now()
            return State.STARTED

        if self.isPaused():
            self.state = 1;
            self.when  = now()
            return State.RESUMED

        return None


class Session():

    def __init__(self, display):
        self.display = display
        self.splits  = None
        self.state   = State()
        self.splits  = []

    def createSplits(self, intensity, duration, distance):
        self.splits = [[duration*60, distance]]
        self.state.reset()
        return True

    def startSplits(self):
        if len(self.splits) > 0:
            self.display.configureSplit(self.splits[0][0], self.splits[0][1])
            self.splits.pop(0)
        self.state.reset()
        return True

    def update(self, speed, strokeRate, heartRate):
        self.display.heartBeat()

        stateChange = self.state.update(speed)
        if stateChange is not None:
            self.display.updateStatus("")
            if stateChange == State.STARTED:
                self.display.start()
            if stateChange == State.PAUSED:
                self.display.pause()
            if stateChange == State.RESUMED:
                self.display.resume()
            if stateChange == State.STOPPED:
                self.display.stop()
                                
        self.display.updateStrokeRate(strokeRate)
        if self.display.updateSpeed(speed):
            # Move to the next split
            if len(self.splits) > 0:
                self.startSplits;
            else:
                self.abort()
                
        self.display.updateHeartBeat(heartRate)

        if self.state.isPaused():
            countDown = self.state.maxPause - self.state.hasBeenFor()
            if countDown >= 0:
                self.display.updateStatus("PAUSED {:d}:{:02d}...".format(int(countDown/60), countDown % 60), 'red')

        self.display.update()

    def abort(self):
        self.state.abort()
