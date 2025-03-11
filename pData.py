import sys
import os
import time
 # Load the required external libs
sys.path.append("apps/python/pData/deps/stdlib64")
sys.path.append("apps/python/pData/deps")
os.environ["PATH"] = os.environ["PATH"] + ";."

import ac
from LapController import LapController, SESSION_LUT
import acsys
import math
from sim_info import info

outfile = None
updatetime=0
lap_number=0
last_meter = None
lap_data = None

dist_threshold = 0.1 # The threshold to say 'this is a valid distance for this meter' 

def toggle_check(checkbox, value):
    global lapController
    if checkbox == "Export Log Files":
        lapController.toggle_log(value)
        return
    if checkbox == "Upload to Cloud":
        lapController.toggle_upload(value)


def init_app(app_label):
    app = ac.newApp(app_label)
    ac.setTitle(app, 'pData Logger')
    ac.setSize(app, 180, 100)
    ac.setIconPosition(app, -100, -100)

    cb_log = ac.addCheckBox(app, "Export Log Files")
    ac.setSize(cb_log, 18, 18)
    ac.setPosition(cb_log, 10, 35)
    ac.addOnCheckBoxChanged(cb_log, toggle_check)
    ac.setValue(cb_log, 0)

    cb_upload = ac.addCheckBox(app, "Upload to Cloud")
    ac.setSize(cb_upload, 18, 18)
    ac.setPosition(cb_upload, 10, 55)
    ac.addOnCheckBoxChanged(cb_upload, toggle_check)
    ac.setValue(cb_upload, 1)
    toggle_check("Upload to Cloud", 1) # Simulate a value change to trigger the listener

def acMain(ac_version):
    global track_length, lapController
    ac.log(sys.version)  
    track = ac.getTrackName(0)
    track_length = ac.getTrackLength(0)
    track_config = ac.getTrackConfiguration(0)
    if track_config and track_config != track: track = "{} {}".format(track, track_config)
    car_name = ac.getCarName(0)

    session_type = info.graphics.session
    driver = ac.getDriverName(0)
    lapController = LapController(session_type, track, round(track_length), car_name, driver)
    ac.log(str(SESSION_LUT[session_type][1] +": "+track + "({}m) in " + car_name).format(track_length))
    app = init_app('pData')
    return "pData"


def acUpdate(deltaT):
    global last_meter
    global track_length
    global lap_number, lap_data
    global lapController
    global session_id


    # TODO: Test? 
    time.sleep(0.001)

    current_s_id = info.graphics.session
    if current_s_id != lapController.session_id: 
        ac.log("Ending session {}".format(lapController.get_session()))
        ac.log("Starting session {}".format(current_s_id))
        lapController.start_session(current_s_id)
    track_distance = round(ac.getCarState(0, acsys.CS.NormalizedSplinePosition) * track_length, 2)
    track_meter = math.floor(track_distance)
    
    if last_meter == track_meter:
        # ac.console("Dupe Discard")
        # We've already measured this meter - discard it
        return
    if track_distance <= (track_meter + 0.4): 
        # This point is too early in the meter - discard it
        # ac.console("Early Discard: {} < {} + 0.5".format(track_distance, track_meter))
        return
    # We have a good distance! Track it.

    last_meter = track_meter

    lap = ac.getCarState(0, acsys.CS.LapCount)
    # ac.console("Meter {} Lap {}".format(track_distance, lap))
    if lap != lapController.current_lap:
        # New Lap Detected - is it a new session?
        if lap == 1:
            ac.log("Ending Session {} - LAP DETECTION".format(lapController.get_session()))
            lapController.start_session(current_s_id)
        else:
            last_time = ac.getCarState(0, acsys.CS.LastLap)
            lapController.start_lap(lap, last_lap_time=last_time)

    tyres_out = info.physics.numberOfTyresOut
    invalid = True if tyres_out > 2 else False
    pit = ac.isCarInPitlane(0)
    speed = round(ac.getCarState(0, acsys.CS.SpeedKMH), 2)
    lap_time = ac.getCarState(0, acsys.CS.LapTime)
    gas = round(ac.getCarState(0, acsys.CS.Gas), 2)
    brake = round(ac.getCarState(0, acsys.CS.Brake), 2)
    gear = ac.getCarState(0, acsys.CS.Gear)
    steer = round(ac.getCarState(0, acsys.CS.Steer), 2)
    rpm = round(ac.getCarState(0, acsys.CS.RPM), 2)
    raw_pos = ac.getCarState(0, acsys.CS.WorldPosition)
    pos = [round(raw_pos[0],1), round(raw_pos[1], 1), round(raw_pos[2], 1)]
    # pos = [round(raw_pos,1) for raw_pos in pos]


    update_info = {
        'lapTime': lap_time,
        'speed': speed,
        'gas': gas, 
        'brake': brake,
        'gear': gear,
        'steer': steer,
        'rpm': rpm,
        'pos': pos, 
        # 'distance': track_distance, # Remove track distance, stick to indices for measurement 
        # 'pit': pit,
        # 'invalid': invalid,
    }

    # info_str = json.dumps(update_info)
    # ac.console(info_str)
    
    lapController.add_lap_data(track_meter-1, update_info) # Shift the meter by 1 for track index - as tracks seem to start at 1m? 
    if invalid: lapController.invalidate_lap()
    if pit: lapController.set_pit_lap()

def acShutdown():
    global lapController
    ac.console('Ending the session')
    lapController.end_event()
    pass
