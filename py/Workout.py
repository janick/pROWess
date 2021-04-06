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

import asyncio
import time

import User


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
        self.maxPause = 5*User.secsInOneMin

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
        self.display  = display
        self.phases   = []
        self.state    = State()
        self.newPhase = None


    def setFuture(self, newPhase):
        self.newPhase = newPhase
        

    # A workout is composed of a series of phases. Each phase ends up being programmed (and run) as a separate
    # workout in the PM-5. Warm-up and cool-down phases are automatically added.
    def createPhases(self, intensity, duration, distance):
        if intensity == "TestProgram":

            self.phases = [{'name':     "Test Warm-up",
                            'duration': 0.50,
                            'restTime': 0,
                            'repeat':   1},
                           {'name':     "Test Program",
                            'duration': 0.50,
                            'restTime': 0.25,
                            'repeat':   3},
                           {'name':     "Test Cool-down",
                            'duration': 0.50,
                            'restTime': 0,
                            'repeat':   0}]
            
        else:
            if duration is None:
                self.phases = [{'name':     "Timed " + intensity,
                                'duration': duration,
                                'restTime': 0,
                                'repeat':   1}]
            else:
                self.phases = [{'name':     intensity + " Distance",
                                'distance': distance,
                                'restTime': 0,
                                'repeat':   1}]

            # Add warm-up and cool-down
            self.phases.insert(0, {'name':     "Warm-up",
                                   'duration': 2,
                                   'restTime': 0,
                                   'repeat':   1})

            self.phases.append({'name':     "Cool-down",
                                'duration': 2,
                                'restTime': 0,
                                'repeat':   1})
        self.state.reset()
        return True

    def startNextPhase(self):
        if len(self.phases) <= 0:
            return None
        
        phase = self.phases.pop(0)
        if 'duration' in phase:
            self.display.configureEndGoal((phase['duration'] + phase['restTime']) * phase['repeat'], None);
            self.display.configurePhase((phase['duration'] + phase['restTime']) * phase['repeat'], None)
        else: 
            self.display.configureEndGoal(None, phase['distance'] * phase['repeat']);
            self.display.configurePhase(None, phase['distance'])
            
        self.display.updateStatus(phase['name'])
        self.state.reset()
        return phase

    def update(self, speed, strokeRate, heartRate):
        rc = None
        
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
            if len(self.phases) > 0:
                # Return the new program to send to the PM-5
                rc = self.phases[0]
                self.startNextPhase()
            else:
                self.abort()
                
        self.display.updateHeartBeat(heartRate)

        if self.state.isPaused():
            countDown = self.state.maxPause - self.state.hasBeenFor()
            if countDown >= 0:
                self.display.updateStatus("PAUSED {:d}:{:02d}...".format(int(countDown/60), countDown % 60), 'red')

        self.display.update()
        return rc

    def abort(self):
        self.newPhase.set_result(None)
        self.state.abort()
