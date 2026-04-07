import sys
import os
import threading
import time

 # Load the required external libs
sys.path.append("apps/python/pData/deps/stdlib64")
sys.path.append("apps/python/pData/deps")
os.environ["PATH"] = os.environ["PATH"] + ";."

import ac
from apps.python.pData.SessionController import SessionController, TELEMETRY_POINTS, SESSION_LUT
from apps.python.pData.DataUploader import stop_worker
import acsys
import math
from sim_info import info
from apps.python.pData.plogging import log
from data_displays import InvalidLapDisplay

outfile = None
updatetime=0
lap_number=1
last_meter = None
lap_data = None
invalid_lap_display = None
session_controller = None

# Midpoint-nearest sampling state
best_meter_delta = None  # best (smallest) delta-from-midpoint seen for the current meter



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
    global session_controller
    global session_id
    global invalid_lap_display
    global best_meter_delta

    # Skip update if app wasn't initialized (e.g., in replay mode)
    if session_controller is None:
        if info.graphics.status == 2:
            initReportingApps()
        else:
            return

    current_s_id = info.graphics.session
    if current_s_id != session_controller.session_id: 
        log("[ac] Ending session {}".format(session_controller.get_session()))
        log("[ac] Starting session {}".format(current_s_id))
        session_controller.start_session(current_s_id)
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
        if lap != session_controller.current_lap:
            if invalid_lap_display:
                invalid_lap_display.clear()
            if lap == 0:
                ac.log("[ac] Ending Session {} - LAP DETECTION".format(session_controller.get_session()))
                session_controller.start_session(current_s_id)
            else:
                last_time = ac.getCarState(0, acsys.CS.LastLap)
                session_controller.start_lap(lap, lap_time=last_time)
    
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
    ers = round(info.physics.kersCurrentKJ, 2)

    session_controller.add_lap_data(track_meter - 1, {  # -1: tracks start at 1m
        TELEMETRY_POINTS.lapTime: lap_time,
        TELEMETRY_POINTS.speed: speed,
        TELEMETRY_POINTS.gas: gas,
        TELEMETRY_POINTS.brake: brake,
        TELEMETRY_POINTS.gear: gear,
        TELEMETRY_POINTS.steer: steer,
        TELEMETRY_POINTS.rpm: rpm,
        TELEMETRY_POINTS.posX: pos[0],
        TELEMETRY_POINTS.posY: pos[1],
        TELEMETRY_POINTS.posZ: pos[2],
        TELEMETRY_POINTS.ers: ers,
    })
    best_meter_delta = meter_delta

    if invalid:
        # Mark lap invalid and update the display
        session_controller.invalidate_lap()
        invalid_lap_display.show(session_controller.current_lap)

    # Update pit state display (shows/hides pit message)
    invalid_lap_display.set_pit(session_controller.current_lap, pit)
    if pit: session_controller.set_pit_lap()

def acShutdown():
    global session_controller
    session_controller.end_event()
    stop_worker()
    log("[ac] Waiting for {} open threads...".format(threading.active_count()))
    for thread in threading.enumerate():
        if thread.name.startswith("pdata"):
            log('[ac] Waiting for thread {}'.format(thread.name))
            thread.join(10)



def initReportingApps():
    global track_length, session_controller, invalid_lap_display

    circuit = ac.getTrackName(0)
    track_length = ac.getTrackLength(0)
    track = ac.getTrackConfiguration(0)
    car_name = ac.getCarName(0)

    session_type = info.graphics.session
    driver = ac.getDriverName(0)
    session_controller = SessionController(session_type, circuit, track, round(track_length), car_name, driver)
    log(str(SESSION_LUT[session_type][1] +": "+circuit+ "-{} ({}m) in " + car_name).format(track, track_length))
    ac.newApp('pData')

    # Initialize data displays (they create their own app windows)
    invalid_lap_display = InvalidLapDisplay()
    
