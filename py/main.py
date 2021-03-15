import asyncio
import binascii
import platform
import uuid

client  = None

from bleak import discover
from bleak import BleakClient, BleakScanner


async def discoverRower():
    devices = await discover()
    for device in devices:
        if 'PM5' in device.name:
            return device
    return None


async def poll(rower, charact):
    async with BleakClient(rower) as client:
        for _ in range(5): 
            val = await client.read_gatt_char(charact)
            print(binascii.hexlify(val))

            
loop = asyncio.get_event_loop()
rower = loop.run_until_complete(discoverRower())
if rower is None:
    print("ERROR: Rower not found")
    exit

loop.run_until_complete(poll(rower, uuid.UUID('{ce060032-43e5-11e4-916c-0800200c9a66}')))
print("Done.")
