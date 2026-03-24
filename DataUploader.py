import threading
import queue
import traceback

import ac
from plogging import log
from ext_requests import handle_lap, send_track_check

_task_queue = queue.Queue()


def _worker_loop():
    log("[uploader] worker started")
    while True:
        task = _task_queue.get()
        if task is None:
            log("[uploader] worker stopping")
            break
        try:
            task()
        except Exception as e:
            log("[uploader] task error: {}".format(traceback.format_exc()))
    log("[uploader] worker stopped")


_worker = threading.Thread(name='pdata_uploader', target=_worker_loop)
_worker.daemon = False
_worker.start()


def stop_worker():
    _task_queue.put(None)


def dispatch_track_check(details_json, track_name):
    log("[uploader] track check dispatched: {}".format(track_name))
    _task_queue.put(lambda: send_track_check(details_json, track_name))


class LapUploader:
    def __init__(self, session_data):
        self.session_data = session_data
        log("[uploader] Initialised")

    def reset(self):
        self.session_data = None

    def _upload_lap(self, lap_data = {}):
        payload = dict(lap_data) if lap_data else {}
        if lap_data:
            log("[request] POST lap: lap={}".format(payload.get('lapNumber')))
            payload['sessionData'] = self.session_data
        handle_lap(payload)

    def dispatch_lap(self, lap_data):
        if lap_data:
            log("[uploader] lap {} dispatched".format(lap_data.get('lapNumber')))
        else: 
            log("[uploader] Sending Session Handshake")
        ac.ext_perfBegin("pdata_lap_queue")
        _task_queue.put(lambda: self._upload_lap(lap_data))
        ac.ext_perfEnd("pdata_lap_queue")
