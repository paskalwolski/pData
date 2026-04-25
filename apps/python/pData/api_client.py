import json

import requests
from requests import HTTPError, Response

from exceptions import APIException

LAP_POST_URL = ""
SESSION_CLOSE_URL = ""

HEADERS = {"Content-Type": "application/json"}


def post_lap(lap_payload):
    # type: (dict) -> tuple[str, str | None]
    data = json.dumps(lap_payload)
    res = _post(LAP_POST_URL, data)
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
    pass


def close_session(session_payload):
    # type: (dict) -> bool
    data = json.dumps(session_payload)
    res = _post(SESSION_CLOSE_URL, data)
    return res.ok


def _post(url, data):
    # type: (str, str) -> Response
    for attempt in range(2):
        try:
            r = requests.post(url, data=data, headers=HEADERS)
            r.raise_for_status()
            return r
        except requests.exceptions.ConnectionError as e:
            if attempt == 1:
                raise APIException("Failed POST retry") from e
        except HTTPError as e:
            raise APIException("Failed POST request") from e
    raise APIException("Failed POST")
