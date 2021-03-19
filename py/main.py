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
import logging
import binascii
import os
import platform
import struct
import time
import uuid

import Display

import aiotkinter


stats               = {}

from bleak import discover
from bleak import BleakClient
from bleak import _logger as bleakLogger


def now():
    return int(time.time())


class WorkoutState:
    #
    # Idle -> Working out -> pause -> working out -> pause -> Ended
    #   0          1           2          1            2       3
    
    def __init__(self):
        self.state = 0
        self.when  = now()

    def start(self):
        self.state = 1
        self.when  = now()
        
    def pause(self):
        self.state = 2;
        self.when  = now()

    def hasBeenPausedFor(self):
        if self.state != 2:
            return 0
        return now() - self.when

    def stop(self):
        self.state = 3
        self.when  = now()

    def isIdle(self):
        return self.state == 0 or self.state == 3

    def isRunning(self):
        return self.state == 1

    def isPaused(self):
        return self.state == 2

    def isEnded(self):
        return self.state == 3


workoutState = WorkoutState()


def decodeCSAFE(val):
    rsp = unframeCSAFE(val)
    if len(rsp) < 2:
        return
    
    if rsp[1][0] == 0x94:
        print("Serial No: " + "".join(chr(n) for n in rsp[1][1]))
        return
    
    print("CSAFE RSP: ", rsp)

    
def decodeRowingStatus(charHandle, val):
    global stats
    
    vals = struct.unpack('<HBHBBBBBBHBHBBB', val)
    
    stats['ElapsedTime']   = (vals[1] << 16) + vals[0]
    stats['Distance']      = (vals[3] << 16) + vals[2]
    stats['WorkoutType']   = vals[4]
    stats['IntervalType']  = vals[5]
    stats['WorkoutState']  = vals[6]
    stats['RowingState']   = vals[7]
    stats['StrokeState']   = vals[8]
    stats['TotalDistance'] = (vals[10] << 16) + vals[9]
    stats['Duration']      = (vals[12] << 16) + vals[11]
    stats['DurationType']  = vals[13]
    stats['DragFactor']    = vals[14]
    
    print(stats)

    
def decodeRowingStatus1(charHandle, val):
    global stats
    
    vals = struct.unpack('<HBHBBHHHBHB', val)
    
    stats['ElapsedTime'] = (vals[1] << 16) + vals[0]
    stats['Speed']       = vals[2]
    stats['StrokeRate']  = vals[3]
    stats['HeartBPM']    = vals[4]
    stats['Pace']        = vals[5]
    stats['AvgPace']     = vals[6]
    stats['RestDist']    = vals[7]
    stats['RestTime']    = (vals[9] << 16) + vals[8]
    
    print(stats)
    

lastElapsedTime = None
def updateRowingStatus1(charHandle, val):
    global window
    global lastElapsedTime
    
    vals = struct.unpack('<HBHBBHHHBHB', val)

    elapsedTime = (vals[1] << 16) + vals[0]
    speed       = vals[2]/1000

    # When rowing stops, elasped time stops, but speed keeps the last value
    if speed > 0 and elapsedTime == lastElapsedTime:
        speed = 0
    lastElapsedTime = elapsedTime
    
    if speed == 0:
        if workoutState.isRunning():
            workoutState.pause()
            window.pauseWorkout()
            window.updateStatus("PAUSED 10...", 'red')
        else:
            if workoutState.isPaused():
                t = 10 - workoutState.hasBeenPausedFor()
                if t <= 0:
                    window.stopWorkout()
                    workoutState.stop()
                else:
                    window.updateStatus("PAUSED " + str(t) + "...", 'red')
    else:
        if workoutState.isIdle():
            workoutState.start()
        else:
            if workoutState.isPaused():
                workoutState.start()
                window.resumeWorkout()

    window.updateStrokeRate(vals[3])
    window.updateSpeed(speed)
    window.updateHeartBeat(vals[4])
    window.heartBeat()


PM5UUID = {'getSerial'  : uuid.UUID('{ce060012-43e5-11e4-916c-0800200c9a66}'),
           'sendCSAFE'  : uuid.UUID('{ce060021-43e5-11e4-916c-0800200c9a66}'),
           'getCSAFE'   : uuid.UUID('{ce060022-43e5-11e4-916c-0800200c9a66}'),
           'RowStatus'  : uuid.UUID('{ce060031-43e5-11e4-916c-0800200c9a66}'),
           'RowStatus1' : uuid.UUID('{ce060032-43e5-11e4-916c-0800200c9a66}')}


#
# Frame a CSAFE command string, adding start, checksum, and stop code
# as well as escaping control bytes
#
def frameCSAFE(cmdBytes):
    frame = [0xF1]
    for b in cmdBytes:
        if 0xF0 <= b and b <= 0xF3:
            frame.append(0xF3)
            frame.append(b - 0xF0)
        else:
            frame.append(b)
    csum = 0x00
    for i in range(1, len(frame)):
        csum = csum ^ frame[i]
    frame.append(csum)
    frame.append(0xF2)
    # print("CSAFE CMD: [" + ", ".join(hex(n) for n in frame) + "]")
    return frame


#
# Parse a CSAFE response frame into an array of per-command response
# First array element is the status, then all subsequent array element
# are two-elements arrays with the command code and the response string for that command
# e.g.
#      [status,
#       [cmdId, [rsp ... rsp ]],
#       ...
#       [cmdId, [rsp ... rsp ]]]
#
def unframeCSAFE(rspBytes):
    # print("CSAFE RSP: [" + ", ".join(hex(n) for n in rspBytes) + "]")
    if rspBytes[0] != 0xF1:
        return None
    rsp = [rspBytes[1]]   # Status
    i = 2;
    while i < len(rspBytes)-2:
        cmd = [rspBytes[i], []]
        i = i + 1
        rspLen = rspBytes[i]
        i = i + 1
        for j in range(rspLen):
            if i >= len(rspBytes)-1:
                return rsp
            datum = rspBytes[i]
            i = i + 1
            if datum == 0xF3:
                datum = rspBytes[i] + 0xF0
                i = i + 1
            cmd[1].append(datum)
        rsp.append(cmd)

    return rsp

    
async def findRower():
    devices = await discover()
    for device in devices:
        if 'PM5' in device.name:
            return device
    return None


async def runRower(rower):
    async with BleakClient(rower) as client:
        val = await client.read_gatt_char(PM5UUID['getSerial'])
        print("Connected to PM5 Serial no " + val.decode())

        charHandlerByHandle = {}
        
        # charHandlerByHandle[client.services.get_characteristic(PM5UUID['getCSAFE'  ]).handle] = decodeCSAFE
        # charHandlerByHandle[client.services.get_characteristic(PM5UUID['RowStatus' ]).handle] = decodeRowingStatus
        # charHandlerByHandle[client.services.get_characteristic(PM5UUID['RowStatus1']).handle] = decodeRowingStatus1

        charHandlerByHandle[client.services.get_characteristic(PM5UUID['RowStatus1']).handle] = updateRowingStatus1
        
        for charHandle in charHandlerByHandle.keys():
            await client.start_notify(charHandle, charHandlerByHandle[charHandle])
            
        window.updateStatus("Start rowing!")

        # Get the serial No via CSAFE
        # await client.write_gatt_char(PM5UUID['sendCSAFE'], frameCSAFE([0x94]), True)
        while not workoutState.isEnded():
            await asyncio.sleep(1)

        print("Disconnecting from rower...")
        for charHandle in charHandlerByHandle.keys():
            val = await client.stop_notify(charHandle)


# Wake up a sleeping screen
os.system('xset s reset')

window = Display.MainDisplay(1100, 1680)

asyncio.set_event_loop_policy(aiotkinter.TkinterEventLoopPolicy())
loop = asyncio.get_event_loop()

rower = loop.run_until_complete(findRower())
if rower is None:
    print("No PM5 rower found")
    window.updateStatus("No PM5 rower found", 'red')
    window.update()
    time.sleep(5)
else:
    window.updateStatus("Connected", 'green')

    loop.run_until_complete(runRower(rower))
    time.sleep(30)

# Put the screen to sleep
os.system('xset dpms force off')
