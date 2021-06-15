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

import Display
import os
import User

#
# Test the display layout
#
data = [[21, 2570, 72],
        [18, 2570, 80],
        [11, 2570, 88],
        [27, 2570, 94],
        [28, 2570, 99],
        [25, 2570, 106],
        [11, 2570, 133],
        [1, 2570, 128],
        [21, 2570, 72]]

progress = 10;

def test():
    global window
    global progress
    if len(data) == 0:
        return

    window.updateStrokeRate(data[0][0])
    window.updateSpeed(data[0][1]/1000)
    window.updateHeartBeat(data[0][2])
    window.progress.updatePercent(progress)
    progress = progress + 10;

    data.pop(0)
    window.after(1000, test)


def beat():
    global window
    window.heartBeat()
    window.after(500, beat)


User.defineUser()

window = Display.MainDisplay(User.screen['X'], User.screen['Y'])
window.configureEndGoal(1, None)
#window.configureSplit(30, None)
window.start()
window.after(1000, test)
window.after(1000, beat)
window.mainloop()

