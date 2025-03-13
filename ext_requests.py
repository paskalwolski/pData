import json
import requests
import ac

from logging import log

headers = {'Content-Type': 'application/json'} # Required to call 'requests.post()' with 'data' param (pre 'json' version)

def send_session_data(string_data, url):
    log("starting data send")
    try:
        r = requests.post(url, data=string_data, headers=headers)
        session_data = r.json()
        session_id = session_data.get("sessionId", "INVALID")
        log("All Done: {}".format(session_id))
    except Exception as e: 
        log("Something went wrong: {}".format(e))


def send_track_check(url, file_data):
    try:
        r = requests.post(url, files=file_data, headers=headers)
        track_data = r.json()
        track_exists = track_data["exists"]
    except Exception as e:
        log("Something went wrong: {}".format(e))

def test_multi():
    hello = requests.get("https://helloworld-3gpdongoba-uc.a.run.app")
    log(hello.text)


