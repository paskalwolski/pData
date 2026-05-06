import json

import requests


from src.models import LapPayload, TrackPayload
from src.exceptions import APIException

LAP_POST_URL = "https://handlelap-3gpdongoba-uc.a.run.app"
SESSION_CLOSE_URL = "https://closesession-3gpdongoba-uc.a.run.app"
TRACK_POST_URL = "https://handletrackdata-3gpdongoba-uc.a.run.app"

HEADERS = {"Content-Type": "application/json"}


def post_lap(lap_data_request):
    # type: (LapPayload) -> tuple[str, str | None]
    """
    Handle a valid Lap that needs to be stored.

    The backend also handles the Session associated - based on the presence of the 'sessionId' key
    a new Session Doc is created, or the old one associated with the Lap
    """
    res = _post(LAP_POST_URL, lap_data_request.to_json())
    if res.status_code == 202:
        # Data wasn't processed correctly - expected a 200
        raise APIException("Payload incorrectly processed: received 202 code")
    if res.status_code == 200:
        try:
            d = res.json()  # type: dict[str, str]
            lap = d["lapId"]
            session = d.get("sessionId", None)
            return lap, session
        except (ValueError, KeyError) as e:
            raise APIException("Malformed Lap Response") from e
    raise APIException("Unexpected Response: {}".format(res.status_code))


def init_lap_handler():
    """
    Empty request to the lap handler to help with spinup and
    opening connection - as this may cause stutters mid-session
    """
    res = _post(LAP_POST_URL, None)
    if not res.status_code == 202:
        raise APIException("Error opening connection to Lap Handler")


def close_session(session_payload):
    # type: (dict) -> bool
    """
    Notify the backend that this Session is closed.
    Can be used to trigger extra Session data calculation
    """
    data = json.dumps(session_payload)
    res = _post(SESSION_CLOSE_URL, data)
    return res.ok


def post_track_data(track_data_request):
    # type: (TrackPayload) -> None
    res = _post(TRACK_POST_URL, track_data_request.to_json())
    if not res.ok:
        raise APIException("Error Posting Track Data: {}".format(res.status_code))


def _post(url, data):
    # type: (str, str | None) -> requests.Response
    for attempt in range(2):
        try:
            r = requests.post(url, data=data, headers=HEADERS, timeout=30)
            r.raise_for_status()
            return r
        except requests.exceptions.ConnectionError as e:
            if attempt == 1:
                raise APIException("Failed POST retry") from e
        except requests.HTTPError as e:
            raise APIException("Failed POST request") from e
    raise APIException("Failed POST")
