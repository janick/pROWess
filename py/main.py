import asyncio
import logging
import binascii
import platform
import struct
import uuid

charDecoderByHandle = {}
stats       = {}

from bleak import discover
from bleak import BleakClient
from bleak import _logger as bleakLogger

def decodeRowingStatus(val):
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
    
def decodeRowingStatus1(val):
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
    

async def discoverRower():
    global charDecoderByHandle
    devices = await discover()
    for device in devices:
        if 'PM5' in device.name:
            async with BleakClient(device) as client:
                charDecoderByHandle[client.services.get_characteristic(uuid.UUID('{ce060031-43e5-11e4-916c-0800200c9a66}')).handle] = decodeRowingStatus
                charDecoderByHandle[client.services.get_characteristic(uuid.UUID('{ce060032-43e5-11e4-916c-0800200c9a66}')).handle] = decodeRowingStatus1
            return device
    return None


def charUpdate(charHandle, data):
    if charHandle in charDecoderByHandle:
        charDecoderByHandle[charHandle](data)
        return
    print(charHandle);
    print("Update from unknown characteristic" + str(charHandle))

    
async def init(rower):
    async with BleakClient(rower) as client:
        print("Connected to rower...")
        for charHandle in charDecoderByHandle.keys():
            val = await client.read_gatt_char(charHandle)
            charDecoderByHandle[charHandle](val)

            """
        val = await client.read_gatt_char(uuid.UUID('{00002902-0000-1000-8000-00805f9b34fb}'))
        print(binascii.hexlify(val))
        await client.write_gatt_char(uuid.UUID('{00002902-0000-1000-8000-00805f9b34fb}'), bytes([0x01, 0x00]))
        val = await client.read_gatt_char(uuid.UUID('{00002902-0000-1000-8000-00805f9b34fb}'))
        print(binascii.hexlify(val))
            """
            
        for charHandle in charDecoderByHandle.keys():
            val = await client.start_notify(charHandle, charUpdate)


async def run():
    print("Running...");
    await asyncio.sleep(10.0)


async def shutdown(rower):
    print("Disconnecting from rower...")
    async with BleakClient(rower) as client:
        for charHandle in charDecoderByHandle.keys():
            val = await client.stop_notify(charHandle)

import sys

            
loop = asyncio.get_event_loop()
rower = loop.run_until_complete(discoverRower())
if rower is None:
    print("ERROR: Rower not found")
    exit
loop.run_until_complete(init(rower))
loop.run_until_complete(run())
loop.run_until_complete(shutdown(rower))

print("Done.")
