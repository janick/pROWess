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
import json
import os
import platform
import struct
import sys
import time
import uuid

import User
import Workout
import Display

import aiotkinter




#
# AWS IoT
#
from AWSIoTPythonSDK.MQTTLib import AWSIoTMQTTShadowClient


thingName = "MyRower"
clientId  = "pROWess"
host      = "a2oc0d7o6qxm4z-ats.iot.us-east-1.amazonaws.com"
port      = 8883

HOME = "/home/janick"
rootCAPath      = HOME + "/pROWess/certificates/AmazonRootCA1.pem"
certificatePath = HOME + "/pROWess/certificates/4c4806177e-certificate.pem.crt"
privateKeyPath  = HOME + "/pROWess/certificates/4c4806177e-private.pem.key"
publicKeyPath   = HOME + "/pROWess/certificates/4c4806177e-public.pem.key"

class MyMQTTClient:
    """
    Client to maintain a connection between the Raspberry Pi and the IoT Shadow.
    """
    def __init__(self, display, workout):
        self.display = display
        self.workout = workout
        
        self.shadowClient = AWSIoTMQTTShadowClient(clientId)

        self.shadowClient.configureEndpoint(host, port)
        self.shadowClient.configureCredentials(rootCAPath, privateKeyPath, certificatePath)
        self.shadowClient.configureAutoReconnectBackoffTime(1, 32, 20)
        self.shadowClient.configureConnectDisconnectTimeout(10)
        self.shadowClient.configureMQTTOperationTimeout(1)

        self.display.updateStatus("Connecting to AWS IoT...")
        self.display.update()
        self.shadowClient.connect()

        self.shadowHandler = self.shadowClient.createShadowHandlerWithName(thingName, True)
        self.shadowHandler.shadowRegisterDeltaCallback(self.delta_callback)
        self.gotoIdle()

        self.display.updateStatus("")
        self.display.update()

        
    def isIdle(self):
        return self.shadowState['intensity'] == "Idle"


    def gotoIdle(self):
        self.shadowState = {'intensity': "Idle", 'duration': None, 'distance': None}
        update = {'state': {'reported': self.shadowState, 'desired': self.shadowState}}
        self.shadowHandler.shadowUpdate(json.dumps(update), None, 5)
    
        
    def delta_callback(self, payload, token, arg):
        delta = json.loads(payload)['state']
        print("Delta: ", delta)

        if 'duration' in delta:
            self.shadowState['duration'] = delta['duration']
        if 'distance' in delta:
            self.shadowState['distance'] = delta['distance']
                
        if 'intensity' in delta:
            self.gotoNextState(delta['intensity'], delta)

        if self.shadowState['intensity'] == "Idle":
            self.gotoIdle()
            return
        
        update = {'state': {'reported': self.shadowState, 'desired': self.shadowState}}
        self.shadowHandler.shadowUpdate(json.dumps(update), None, 5)


    def gotoNextState(self, nextState, delta):
        # Can go from Idle -> Start new workout
        if self.shadowState['intensity'] == "Idle":
            if nextState in ["Easy", "Normal", "Intense", "Interval", "Cardio", "Strength", "Scheduled"]:
                
                if self.workout.createSplits(nextState, self.shadowState['duration'], self.shadowState['distance']):
                    self.shadowState['intensity'] = nextState
                    return True
                return False

        # Anything else, we're in the middle of a work out.
        # Can only abort
        if nextState == "Abort":
            self.workout.abort()
            self.gotoIdle()
            return True

        # Ignore the command
        return False
                

#
# PM-5 BLE
#


stats               = {}

from bleak import discover
from bleak import BleakClient
from bleak import _logger as bleakLogger


def now():
    return int(time.time())


workoutSession = None


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
    global workoutSession
    global lastElapsedTime
    
    vals = struct.unpack('<HBHBBHHHBHB', val)

    elapsedTime = (vals[1] << 16) + vals[0]
    speed       = vals[2]/1000
    strokeRate  = vals[3]
    heartBeat   = vals[4]

    # When rowing stops, elasped time stops, but speed keeps the last value
    if speed > 0 and elapsedTime == lastElapsedTime:
        speed = 0
    lastElapsedTime = elapsedTime

    workoutSession.update(speed, strokeRate, heartBeat)


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
        window.update()

        # Get the serial No via CSAFE
        # await client.write_gatt_char(PM5UUID['sendCSAFE'], frameCSAFE([0x94]), True)
        while not workoutSession.state.isEnded():
            await asyncio.sleep(1)

        
        window.updateStatus("Disconnecting...")
        window.update()
        await asyncio.sleep(1)
        for charHandle in charHandlerByHandle.keys():
            val = await client.stop_notify(charHandle)


#
# This program runs at all times. Start automatically via /etc/rc script.
#
# In idle state, the screen is powered off and disconnected from the PM5
#
# Alexa, ask MyRower to start an [easy|intense] [n] meters|minutes workout"
#       -> Turn on screen and connects to PM5
#       -> Generate splits, start session
#       "Your workout will start when you start rowing"
#
# "Alexa, open MyRower"
#       -> Turn on screen and connects to PM5
#       "What kind of workout would you like?"
#
#    "Start an [easy|intense] [n] meters|minutes workout"
#       -> Generate splits, start session
#       "Your workout will start when you start rowing"
#
#    "Alexa, tell MyRower to stop my workout"
#       -> Abort workout, go to idle
#
#    "Alexa, tell MyRower to pause my workout"
#       -> Pause workout, without 10 secs abort timer
#       "Your workout will resume when you resume rowing"
#
# At end of workout
#       -> Go to idle
#       See if we can get Alexa to say something
# 


User.defineUser()

for arg in sys.argv:
    if arg == "-d":
        User.secsInOneMin  = 1
        User.metersInOneKm = 10

        
# Wake up a sleeping screen
os.system('xset s reset')


window = Display.MainDisplay(User.screen['X'], User.screen['Y'])
workoutSession = Workout.Session(window)

shadowIoT = MyMQTTClient(window, workoutSession)

asyncio.set_event_loop_policy(aiotkinter.TkinterEventLoopPolicy())
loop = asyncio.get_event_loop()

while True:
    window.updateStatus("Waiting for workout request...")
    window.update()

    startedWaiting = now()
    while shadowIoT.isIdle():
        # Refresh the message every minute
        if (now() - startedWaiting) % 60 == 0:
            window.updateStatus("Waiting for workout request...")
            window.update()
        # Turn off the screen if we've been waiting for a while
        if now() - startedWaiting > 10 * User.secsInOneMin:
            # Put the screen to sleep
            # Needs 'hdmi_blanking=1' in /boot/config.txt
            os.system('xset dpms force off')
        time.sleep(1)
        
    # Wake up a sleeping screen
    os.system('xset s reset')

    window.updateStatus("Connecting to PM5...")
    window.update()

    rower = loop.run_until_complete(findRower())
    if rower is None:
        print("No PM5 rower found")
        window.updateStatus("No PM5 rower found", 'red')
        window.update()
        continue

    window.updateStatus("Connected", 'green')
    window.update()

    workoutSession.startSplits()
    
    loop.run_until_complete(runRower(rower))
    shadowIoT.gotoIdle()
    
    window.updateStatus("Workout done.")
    window.update()
