import asyncio
import platform

rower = None


from bleak import discover

async def discoverRower():
    global rower
    devices = await discover()
    for device in devices:
        if 'PM5' in device.name:
            rower = device
            return


from bleak import BleakClient, BleakScanner

async def print_services(device):
    async with BleakClient(device) as client:
        svcs = await client.get_services()
        print("Services:")
        for service in svcs:
            print(type(service))

            
loop = asyncio.get_event_loop()
loop.run_until_complete(discoverRower())
if rower is None:
    print("ERROR: Rower not found")
    exit

loop.run_until_complete(print_services(rower))
