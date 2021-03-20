import json
import logging

import boto3

import re

logger = logging.getLogger()
logger.setLevel(logging.DEBUG)


#
# Translate AMAZON.DURATION ISO-8601 values into minutes
#
def ISO8601_to_mins(duration):
    mins = 0
    val = 0
    for char in duration:
        if char.isdigit():
            val = (val * 10) + int(char)
            continue
        if char == 'H':
            mins += val * 60
            val = 0
            continue
        if char == 'M':
            mins += val;
        val = 0;
        
    return mins


#                                                                                                                                                                                        
# Response object                                                                                                                                                                        
#                                                                                                                                                                                        
class Response:
    # A response with a corresponding default card                                                                                                                                       
    def __init__(self, title, say, cardText = None):
        self.rsp = {}
        self.rsp['outputSpeech'] = {'type': 'SSML',
                                    'ssml':  "<speak>" + say + "</speak>"}
        if title != None:
            if cardText == None:
                cardText = say

            self.rsp['card'] = {'type': 'Simple',
                                'title': "My Rower - " + title,
                                'content': cardText}
        self.rsp['shouldEndSession'] = True

    # Replace the card with an explicit one                                                                                                                                              
    def card(self, type, args):
        args['type'] = type
        self.rsp['card'] = args

    # Add a reprompt to the response                                                                                                                                                     
    def reprompt(self, say):
        self.rsp['reprompt'] = {'outputSpeech': {'type': 'SSML',
                                                 'ssml':  "<speak>" + say + "</speak>"}}
        self.rsp['shouldEndSession'] = False

    # Keep the session open after this response                                                                                                                                          
    def keepSessionOpen(self):
        self.rsp['shouldEndSession'] = False

    # Elicit the next slot in the dialog                                                                                                                                                 
    def elicit(self, slot):
        self.rsp['directives'] = [ {"type": "Dialog.ElicitSlot",
                                    "slotToElicit": slot} ]


class EventHandler:

    def __init__(self, context, state):
        self.context        = context
        self.state          = state
        self.response       = None

        self.topic          = "$aws/things/MyRower/shadow/update"
        self.shadowClient   = boto3.client('iot-data', 'us-east-1')

    def updateShadow(self, new_value_dict):
        """
        Updates IoT shadow's "desired" state with values from new_value_dict. Logs
        current "desired" state after update.

        Args:
        new_value_dict: Python dict of values to update in shadow
        """
        payload = {
            "state": {
                "desired" : new_value_dict
            }
        }
        response = self.shadowClient.update_thing_shadow(thingName = "MyRower",
                                                         payload   = json.dumps(payload))
        res_payload = json.loads(response['payload'].read().decode('utf-8'))
        
        
    def StartWorkoutTime(self, slots):
        logging.debug("Time: " + json.dumps(slots))
        
        intensity = "Normal"
        if 'value' in self.slots['Intensity']:
            intensity = self.slots['Intensity']['value']

        if 'value' not in self.slots['TotalTime']:
            self.response = Response("Duration",
                                    "Sorry, but I do not understand how long of a workout your want. " +
                                    "What workout or race would you like to start?")
            self.response.keepSessionOpen()
            return True

        duration = ISO8601_to_mins(self.slots['TotalTime']['value'])

        self.updateShadow({'intensity': intensity, 'duration': duration, 'distance': None})
            
        self.response = Response("Workout", "Starting a {} {} minutes workout".format(intensity, duration))
        return True
        
        
    def StartWorkoutDistance(self, slots, units):
        logging.debug("Distance: " + json.dumps(slots))
        
        intensity = "Normal"
        if 'value' in self.slots['Intensity']:
            intensity = self.slots['Intensity']['value']

        if 'value' not in self.slots['TotalDistance']:
            self.response = Response("Duration",
                                    "Sorry, but I do not understand how long a race your want. " +
                                    "What workout or race would you like to start?")
            self.response.keepSessionOpen()
            return True

        distance = int(self.slots['TotalDistance']['value'])
        distance *= units

        # If the distance is too short, ask again
        if distance < 1000:
            self.response = Response("Too Short", "A {} meters race is too short.  ".format(distance) +
                                     "Tell me again what workout or race would you like to start?")
            self.response.keepSessionOpen()
            return True
            

        self.updateShadow({'intensity': intensity, 'duration': None, 'distance': distance})
            
        self.response = Response("Workout", "Starting a {} {} meters race".format(intensity, distance))
        return True


    def StartWorkoutFree(self):
        self.updateShadow({'intensity': "Normal", 'duration': None, 'distance': None})
        self.response = Response("Workout", "Starting a free workout.")
        return True

    
    def StartWorkoutScheduled(self):
        self.updateShadow({'intensity': "Scheduled", 'duration': None, 'distance': None})
        self.response = Response("Workout", "Starting today's scheduled workout.")
        return True

    
    def PauseWorkout(self):
        self.updateShadow({'intensity': "Pause", 'duration': None, 'distance': None})
        self.response = Response("Workout", "Pausing your work-out.")
        return True

    
    def ResumeWorkout(self):
        self.updateShadow({'intensity': "Resume", 'duration': None, 'distance': None})
        self.response = Response("Workout", "Resuming your paused workout.")
        return True

    
    def StopWorkout(self):
        self.updateShadow({'intensity': "Abort", 'duration': None, 'distance': None})
        self.response = Response("Workout", "Stopping your workout.")
        return True

    
    # When the skill gets launched
    def onLaunch(self):
        self.response = Response("Workout", "What workout would you like to start?")
        self.response.keepSessionOpen()
        return True


    # When the skill gets an intent
    def onIntent(self, intent):

        logging.debug(intent['name'])

        self.slots = {};
        if 'slots' in intent:
            self.slots = intent['slots']

        if intent['name'] == "AMAZON.HelpIntent":
            return self.help("")

        if intent['name'] == "WorkoutTime":
            return self.StartWorkoutTime(self.slots)
            
        if intent['name'] == "WorkoutDistanceMeters":
            return self.StartWorkoutDistance(self.slots, 1)
            
        if intent['name'] == "WorkoutDistanceKilometers":
            return self.StartWorkoutDistance(self.slots, 1000)
            
        if intent['name'] == "JustRow":
            return self.StartWorkoutFree()
            
        if intent['name'] == "ScheduledWorkout":
            return self.StartWorkoutScheduled()
            
        if intent['name'] == "PauseWorkout":
            return self.PauseWorkout()
            
        if intent['name'] == "ResumeWorkout":
            return self.ResumeWorkout()
            
        if intent['name'] == "StopWorkout":
            return self.StopWorkout()
            
        self.response = Response("Sorry", "Sorry. Your rower doesn't know how to do that.")
        return False;


    def help(self, prefix):
        self.response = Response("Help", prefix + \
                                "I can connect and monitor a workout on your rowing machine. " + \
                                 "Just ask me to start an easy, normal, or intense 30 minutes or 3000 meters workout. " +
                                 "You can also ask me to pause, resume, or stop a workout in progress.")
        self.response.keepSessionOpen()
        return True


    def onEnd(self):
        return True



    def onRequest(self, request):
        isOK = False
        
        logging.debug(request['type'])
        
        if request['type'] == "LaunchRequest":
            isOK = self.onLaunch()
        elif request['type'] == "IntentRequest":
            isOK = self.onIntent(request['intent'])
        elif request['type'] == "SessionEndedRequest":
            isOK = self.onEnd()
        else:
            logging.error("Unexpected request " + request['type'] + " received.")

        if self.response == None:
            if isOK:
                return None

            self.response = Response("Sorry", "Sorry. Something went wrong")

        return {'version': '1.0',
                'sessionAttributes': self.state,
                'response': self.response.rsp}


def lambda_handler(event, context):
    logging.info("event.session.application.applicationId=" +
                 event['session']['application']['applicationId'])

    """
    Prevent someone else from configuring a skill that sends requests to this function.
    """
    if (event['session']['application']['applicationId'] != "amzn1.ask.skill.4254825f-0ea2-482a-a593-0abd200fc84e"):
        raise ValueError("Invalid Application ID")
    
    attributes = {}
    if 'attributes' in event['session']:
        attributes = event['session']['attributes']

    return EventHandler(event['context'], attributes).onRequest(event['request'])

