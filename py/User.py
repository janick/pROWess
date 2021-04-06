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


#
# User profile variables
#

# Timescales, so we can speed things up in debug mode
secsInOneMin  = 60
metersInOneKm = 1000

# Size of the display windoe
screen = {'X': 1680, 'Y': 1050, 'DPI': 90}

# Average 500m split time, in seconds, to estimate reset time during distance intervals
splitTime = 2*60+30

import socket

def defineUser():
    global secsInOneMin, metersInOneKm, screen

    machine = socket.gethostname()
    if machine == "Janicks-MacBook-Air.local":
        screen = {'X': 1400, 'Y': 8800, 'DPI': 96}
