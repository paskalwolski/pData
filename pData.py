import sys
import os
import threading
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
from plogging import log
from data_displays import InvalidLapDisplay

outfile = None
updatetime=0
lap_number=1
last_meter = None
lap_data = None
invalid_lap_display = None
lapController = None

# Midpoint-nearest sampling state
best_meter_delta = None  # best (smallest) delta-from-midpoint seen for the current meter


def toggle_check(checkbox, value):
    global lapController
    if checkbox == "Export Log Files":
        lapController.toggle_log(value)
        return
    if checkbox == "Upload to Cloud":
        lapController.toggle_upload(value)
    if checkbox == "Upload track data":
        lapController.toggle_track_upload(value)


def init_app(app_label):
    app = ac.newApp(app_label)
    ac.setTitle(app, 'pData Logging Config')
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

    cb_track = ac.addCheckBox(app, "Upload track data")
    ac.setSize(cb_track, 18, 18)
    ac.setPosition(cb_track, 10, 75)
    ac.addOnCheckBoxChanged(cb_track, toggle_check)
    ac.setValue(cb_track, 0)
    toggle_check("Upload track data", 0) # Simulate a value change to trigger the listener

def acMain(ac_version):
    
    
    log(sys.version)  
    # Check if we're in replay mode - if so, disable the app
    if info.graphics.status != 2:
        log("AC is not Live. App disabled.")
        return "pData"

    initReportingApps()
    
    return "pData"


def acUpdate(deltaT):
    global last_meter
    global track_length
    global lap_number, lap_data
    global lapController
    global session_id
    global invalid_lap_display
    global best_meter_delta

    # Skip update if app wasn't initialized (e.g., in replay mode)
    if lapController is None:
        if info.graphics.status == 2:
            initReportingApps()
        else:
            return

    current_s_id = info.graphics.session
    if current_s_id != lapController.session_id: 
        log("Ending session {}".format(lapController.get_session()))
        log("Starting session {}".format(current_s_id))
        lapController.start_session(current_s_id)
    track_distance = round(ac.getCarState(0, acsys.CS.NormalizedSplinePosition) * track_length, 2)
    track_meter = math.floor(track_distance)
    meter_delta = abs((track_distance - track_meter) - 0.5)  # absolute distance from midpoint

    is_new_meter = track_meter != last_meter

    if not is_new_meter:
        # Same meter — skip if this reading is not closer to the midpoint
        if best_meter_delta is not None and meter_delta >= best_meter_delta:
            # Ignore this meter point - we already have a better one
            return

    else:
        # Check for meter and lap change only when we have a new meter
        last_meter = track_meter

        # Lap detection
        lap = ac.getCarState(0, acsys.CS.LapCount) + 1
        if lap != lapController.current_lap:
            if invalid_lap_display:
                invalid_lap_display.clear()
            if lap == 0:
                ac.log("Ending Session {} - LAP DETECTION".format(lapController.get_session()))
                lapController.start_session(current_s_id)
            else:
                last_time = ac.getCarState(0, acsys.CS.LastLap)
                lapController.start_lap(lap, last_lap_time=last_time)
    
    # Read telemetry when we are sure we'll use it
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

    lapController.add_lap_data(track_meter - 1, {  # -1: tracks start at 1m
        'lapTime': lap_time,
        'speed': speed,
        'gas': gas,
        'brake': brake,
        'gear': gear,
        'steer': steer,
        'rpm': rpm,
        'pos': pos,
    })
    best_meter_delta = meter_delta

    if invalid:
        # Mark lap invalid and update the display
        lapController.invalidate_lap()
        invalid_lap_display.show(lapController.current_lap)

    # Update pit state display (shows/hides pit message)
    invalid_lap_display.set_pit(lapController.current_lap, pit)
    if pit: lapController.set_pit_lap()

def acShutdown():
    global lapController
    ac.console('Ending the session')
    lapController.end_event()
    log("Waiting for {} open threads...".format(threading.active_count()))
    for thread in threading.enumerate():
        if thread.name.startswith("pdata"):
            thread.join()



def initReportingApps():
    """Init the lapController"""
    global track_length, lapController, invalid_lap_display

    circuit = ac.getTrackName(0)
    track_length = ac.getTrackLength(0)
    track = ac.getTrackConfiguration(0)
    car_name = ac.getCarName(0)

    session_type = info.graphics.session
    driver = ac.getDriverName(0)
    lapController = LapController(session_type, circuit, track, round(track_length), car_name, driver)
    log(str(SESSION_LUT[session_type][1] +": "+circuit+ "-{} ({}m) in " + car_name).format(track, track_length))
    app = init_app('pData')

    # Initialize data displays (they create their own app windows)
    invalid_lap_display = InvalidLapDisplay()
    
