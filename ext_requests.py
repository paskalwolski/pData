import json
import requests
import ac

headers = {'Content-Type': 'application/json'} # Required to call 'requests.post()' with 'data' param (pre 'json' version)

def send_session_data(s, url):
    ac.log("starting data send")
    try:
        r = requests.post(url, data=json.dumps(s), headers=headers)
        ac.log(r.text)
    except: 
        ac.log("Something went wrong")


def test_multi():
    hello = requests.get("https://helloworld-3gpdongoba-uc.a.run.app")
    ac.log(hello.text)


