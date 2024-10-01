import ac
from LapController import LapController
import acsys
import json

outfile = None
updatetime=0
lap_number=0
distance = None
lap_data = None

def acMain(ac_version):
    global track_length, lapController
    ac.console("Starting the new app")
    
   
    import urllib.request

    url = "http://www.example.com/"

    # Make a GET request
    with urllib.request.urlopen(url) as response:
        status = response.getcode()
        content = response.read().decode()

    ac.log(status)

    track = ac.getTrackName(0)
    track_length = ac.getTrackLength(0)
    session_type = ac.getTrackConfiguration(0)
    car_name = ac.getCarName(0)
    lapController = LapController(session_type, track, car_name)
    ac.log(str(session_type +": "+track + " in " + car_name))
    appWindow = ac.newApp('pData')
    ac.setSize(appWindow, 200, 100)
    return "pData"


def acUpdate(deltaT):
    global distance
    global track_length
    global lap_number, lap_data
    global lapController

    # Take 4 points per meter - we store the first valid clamp dist and discard any new ones for that same clamp dist - even if the raw dist is different  
    track_distance = get_track_distance(track_length, ac.getCarState(0, acsys.CS.NormalizedSplinePosition))
    if not distance: distance = track_distance
    if distance == track_distance:
        # Discard data for the same distance point
        return

    distance = track_distance

    lap = ac.getCarState(0, acsys.CS.LapCount)
    if lap != lap_number:
        ac.log('started new lap')
        lap_number = lap
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
    if not valid: lapController.invalidate_lap()
    if pit: lapController.set_pit_lap()

def acShutdown():
    global lapController
    ac.console('Ending the session')
    lapController.end_session()
    pass

def get_track_distance(track_length, track_position):
    return clamp_track_distance(track_length * track_position)

def clamp_track_distance(dist: float):
    """Take a value and clamp it to a quarter meter"""
    return round(dist * 4) / 4


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