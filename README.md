# Python + tk Concept 2 Rower PM5 Monitor over BLE

Designed for the Raspberry Pi Zero-W and Alexa

```
Copyright 2021 Janick Bergeron <janick@bergeron.com>

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

    http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.
```

### Status

In development

#### Dear Concept2,

I was originally going to keep this repository and project private,
but after attempting to post a question about the BLE API in the
[Concept2 SDK Forum](), my post was rejected because it "*has the only
purpose to advertise for a website or another product*". In fact, I was
asking if anyone had made any progress on the issues reported in
[that post](https://www.c2forum.com/viewtopic.php?f=15&t=194401) and
[that post](https://www.c2forum.com/viewtopic.php?t=93541) because
I ran into the exact same problem.

Good news: I figured out what I was doing wrong.

Turns out you cannot read the PM5 BLE characteristics using the
bleak.backends.client.BaseBleakClient::read_gatt_attr() method, except
for the Device Information Service characteristics (UUIDs
0x0011..0x0016).  The response you'll receive by reading all other
characteritics will have the correct structure (number of bytes, CSAFE
framing, etc...) but the variable content will be junk.  All other
characteristics, including CSAFE command responses, must be read via a
change notification handler.

I also had incorrectly implemented the co-routine necessary to use
Bleak. Python was not giving any run-time errors, but calling regular
subroutines and passing the async manager as argument appears to break things.
The async patterns must be strictly followed.

### What works today

* Discovers and connects to rower
* Receives updates from rowing service every half-seconds.

### To Do

* Display
  1. Design and create on-screen display using Tkinter
  2. Update on-screen widgets based on PM5 state updates
  3. Add target stroke, pace, and heart rate to display widgets
  4. Course map/plot widget based on target/estimated total distance
  5. Add pace boat to course map/plot
* Work-outs
  1. Get "just-row" mode working
  2. Program, then run a work-out
  3. Alexa front-end to start app, program an X minutes or meters work-out
  4. Alexa utterance to pick work-out from pre-defined work-out database
  5. Log workout
* User Profiles
  1. Scale work-out target parameters based on user profile data
  2. Update user profile (age, max heart rate, etc..) via Alexa
* Multi-User


### Requirements
* Python 3.6 or later (required by Bleak)
* Bleak

### References
* [Bleak Github](https://github.com/hbldh/bleak)
* [PM5 BLE Services](https://www.concept2.co.uk/files/pdf/us/monitors/PM5_BluetoothSmartInterfaceDefinition.pdf)    
* [Concept2 SDK (CSAFE spec)](https://www.concept2.com/service/software/software-development-kit)
