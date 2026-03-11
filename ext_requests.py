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

_session = requests.Session()
_session.headers.update(headers)


def create_session(session_data):
    r = _session.post(CREATE_SESSION_URL, data=json.dumps(session_data))
    result = r.json()
    log(result)
    session_id = result.get("sessionId", None)
    log("[request] create_session response: {}".format(session_id))
    return session_id


def handle_lap(lap_data):
    r = _session.post(HANDLE_LAP_URL, data=json.dumps(lap_data))
    log("[request] handle_lap response: {}".format(r.status_code))
    return


def send_session_data(string_data):
    r = _session.post(SESSION_SEND_URL, data=string_data)
    session_data = r.json()
    lap_id = session_data.get('lapId', None)
    session_id = session_data.get("sessionId", None)
    log("Upload: Lap {} Session {}".format(lap_id, session_id))
    return


def send_track_check(track_data_string, track_name):
    track_check_data = json.dumps({"trackName": track_name})
    r = _session.post(TRACK_CHECK_URL, data=track_check_data)
    exists = r.json()['exists']
    if not exists:
        log("Uploading Track Data {}".format(track_name))
        _session.post(TRACK_POST_URL, data=track_data_string)
    else:
        log("Track Data Exists {}".format(track_name))
    return
