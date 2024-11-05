import json
import requests
import ac

headers = {'Content-Type': 'application/json'} # Required to call 'requests.post()' with 'data' param (pre 'json' version)

def send_session_data(string_data, url):
    ac.log("starting data send")
    try:
        r = requests.post(url, data=string_data, headers=headers)
        session_data = r.json()
        session_id = session_data.get("sessionId", "INVALID")
        ac.log("All Done: {}".format(session_id))
    except Exception as e: 
        ac.log("Something went wrong: {}".format(e))


def test_multi():
    hello = requests.get("https://helloworld-3gpdongoba-uc.a.run.app")
    ac.log(hello.text)


