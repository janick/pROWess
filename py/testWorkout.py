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

import sys
import time

import User
import Workout
import Display

User.defineUser()

User.secsInOneMin  = 4
User.metersInOneKm = 10

testMode = 'Free'
for arg in sys.argv:
    if arg == "-Tt":
        testMode = 'Time'
    if arg == "-Td":
        testMode = 'Distance'

        
window = Display.MainDisplay(User.screen['X'], User.screen['Y'])
workoutSession = Workout.Session(window)

if testMode == "Time":
    workoutSession.createSplits("Normal", 30, None)
if testMode == "Distance":
    workoutSession.createSplits("Normal", None, 5000)

workoutSession.startSplits()

interval = 0.5
for i in range(10):
    time.sleep(interval)
    workoutSession.update(0, 0, 78)
for i in range(20):
    time.sleep(interval)
    workoutSession.update(2, 20, 90)
for i in range(6):
    time.sleep(interval)
    workoutSession.update(0, 0, 85)
for i in range(20):
    time.sleep(interval)
    workoutSession.update(2, 20, 90)
for i in range(20):
    time.sleep(interval)
    workoutSession.update(0, 0, 80)
time.sleep(10)

exit(0)
