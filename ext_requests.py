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


def send_session_data(string_data):
    r = requests.post(SESSION_SEND_URL, data=string_data, headers=headers)
    session_data = r.json()
    session_id = session_data.get("sessionId", "INVALID")
    log("Upload: {}".format(session_id))
    return


def send_track_check(track_data_string, track_name):
        track_check_data = json.dumps({"trackName": track_name})
        r = requests.post(TRACK_CHECK_URL, data=track_check_data, headers=headers)
        exists = r.json()['exists']
        if not exists:
            log("Uploading Track Data {}".format(track_name))
            r = requests.post(TRACK_POST_URL, data=track_data_string, headers=headers)
        else:
            log("Track Data Exists {}".format(track_name))
        return
