import sys
import os
 # Load the required external libs
sys.path.append("apps/python/pData/deps/stdlib64")
sys.path.append("apps/python/pData/deps")
os.environ["PATH"] = os.environ["PATH"] + ";."

import ac
from LapController import LapController
import acsys
import json
import requests
import math
from sim_info import info

outfile = None
updatetime=0
lap_number=0
last_meter = None
lap_data = None

dist_threshold = 0.1 # The threshold to say 'this is a valid distance for this meter' 

def acMain(ac_version):
    global track_length, lapController
    ac.console("Starting the new app")   
    track = ac.getTrackName(0)
    track_length = ac.getTrackLength(0)
    track_config = ac.getTrackConfiguration(0)
    if track_config and track_config != track: track = "{} {}".format(track, track_config)
    car_name = ac.getCarName(0)

    session_type = info.graphics.session

    lapController = LapController(session_type, track, car_name)
    ac.log(str(str(session_type) +": "+track + " in " + car_name))
    appWindow = ac.newApp('pData')
    ac.setSize(appWindow, 200, 100)
    return "pData"


def acUpdate(deltaT):
    global last_meter
    global track_length
    global lap_number, lap_data
    global lapController

    current_s_id = info.graphics.session
    if current_s_id != lapController.session_id: 
        ac.log("Ending session {}".format(lapController.get_session()))
        ac.log("Starting session {}".format(current_s_id))
        lapController.start_session(current_s_id)
    track_distance = ac.getCarState(0, acsys.CS.NormalizedSplinePosition) * track_length
    track_meter = math.floor(track_distance)
    # ac.console("{} meter {}".format(track_distance, track_meter))
    if last_meter == track_meter:
        ac.console("Dupe Discard")
        # We've already measured this meter - discard it
        return
    if track_distance <= (track_meter + 0.5): 
        # This point is too early in the meter - discard it
        ac.console("Early Discard: {} < {} + 0.5".format(track_distance, track_meter))
        return
    # We have a good distance! Track it.
    last_meter = track_meter
    ac.log("Using {} for meter {}".format(track_distance, track_meter))

    lap = ac.getCarState(0, acsys.CS.LapCount)
    if lap != lap_number:
        ac.log('started new lap')
        lap_number = lap
        last_time = ac.getCarState(0, acsys.CS.LastLap)
        lapController.end_lap(last_time)
        # More to come here - end the previous dataset, start a new one
        # What happens at end of session? 
    valid = ac.getCarState(0, acsys.CS.LapInvalidated)
    pit = ac.isCarInPitlane(0)
    speed = ac.getCarState(0, acsys.CS.SpeedKMH)
    gas = ac.getCarState(0, acsys.CS.Gas)
    brake = ac.getCarState(0, acsys.CS.Brake)
    gear = ac.getCarState(0, acsys.CS.Gear)
    steer = ac.getCarState(0, acsys.CS.Steer)
    rpm = ac.getCarState(0, acsys.CS.RPM)

    update_info = {
        'distance': track_distance,
        'speed': speed,
        'gas': gas, 
        'brake': brake,
        'gear': gear,
        'steer': steer,
        'rpm': rpm,
    }

    info_str = json.dumps(update_info)
    ac.console(info_str)
    lapController.add_lap_data(update_info)
    if not valid: lapController.invalidate_lap()
    if pit: lapController.set_pit_lap()

def acShutdown():
    global lapController
    ac.console('Ending the session')
    lapController.end_event()
    pass


"""
{
    track_name, 
    session_start_time, 
    laps: [{
        position: [(x, y, z)]
        track_position,
        lap_number, 
        isValid,
        speed, 
        brake, 
        gas, 
        steering,
        gear,
        rpm,
        tc,
    }, ]
}
"""