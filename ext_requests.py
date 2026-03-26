import json
import requests
import ac

from plogging import log

headers = {
    "Content-Type": "application/json"
}  # Required to call 'requests.post()' with 'data' param (pre 'json' version)
TRACK_CHECK_URL = "https://checktrackdata-3gpdongoba-uc.a.run.app"
TRACK_POST_URL = "https://handletrackdata-3gpdongoba-uc.a.run.app"
SESSION_SEND_URL = "https://handlesessionsubmit-3gpdongoba-uc.a.run.app"
CREATE_SESSION_URL = "https://createsession-3gpdongoba-uc.a.run.app"
HANDLE_LAP_URL = "https://handlelap-3gpdongoba-uc.a.run.app"
SESSION_CLOSE_URL = "https://closesession-3gpdongoba-uc.a.run.app"

def _post(url, data):
    for attempt in range(2):
        try:
            return requests.post(url, data=data, headers=headers)
        except requests.exceptions.ConnectionError:
            if attempt == 1:
                raise



def handle_lap(lap_data):
    ac.ext_perfBegin("pdata_lap_dump")
    data = json.dumps(lap_data)
    ac.ext_perfEnd("pdata_lap_dump")
    ac.ext_perfBegin("pdata_lap_send")
    r = _post(HANDLE_LAP_URL, data=data)
    ac.ext_perfEnd("pdata_lap_send")
    log("[request] handle_lap response: {}".format(r.status_code))
    response = r.json()
    lap_id = response.get('lapId', None)
    session_id = response.get('sessionId', None)
    return lap_id, session_id


def send_track_check(track_data_string, track_name):
    track_check_data = json.dumps({"trackName": track_name})
    r = _post(TRACK_CHECK_URL, data=track_check_data)
    exists = r.json()['exists']
    if not exists:
        log("Uploading Track Data {}".format(track_name))
        _post(TRACK_POST_URL, data=track_data_string)
    else:
        log("Track Data Exists {}".format(track_name))
    return

def close_session(session_id, session_lap_count):
    session_close_data = json.dumps({'sessionId': session_id, 'lapCount': session_lap_count})
    r = _post(SESSION_CLOSE_URL, data=session_close_data)
    


