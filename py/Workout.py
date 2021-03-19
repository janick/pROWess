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

    def reset(self):
        self.state = 0
        self.when  = now()

    def isIdle(self):
        return self.state == 0 or self.state == 3

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
        if speed == 0:
            if self.isRunning():
                self.state = 2;
                self.when  = now()
                return State.PAUSED

            if self.isPaused():
                # You have 10 secs to resume a work-out
                if self.hasBeenFor() >= 10:
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

    def __init__(self, display, splits=None):
        self.display = display
        self.splits  = splits
        self.state   = State()
        
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
        self.display.updateSpeed(speed)
        self.display.updateHeartBeat(heartRate)

        if self.state.isPaused():
            countDown = 9 - self.state.hasBeenFor()
            if countDown >= 0:
                self.display.updateStatus("PAUSED {:d}...".format(countDown), 'red')

        self.display.update()
