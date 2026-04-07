import threading
import queue
import traceback

import ac
from apps.python.pData.plogging import log
from apps.python.pData.ext_requests import handle_lap, send_track_check, close_session, send_track_data

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


_worker = threading.Thread(name="pdata_uploader", target=_worker_loop)
_worker.daemon = False
_worker.start()


def stop_worker():
    _task_queue.put(None)


class TrackDataUploader:
    def __init__(self, track_id, check_callback=None):
        self.track_id = track_id
        self.check_callback = check_callback
        self.dispatch_track_check()

    def dispatch_track_check(self):
        log("[uploader] track check dispatched: {}".format(self.track_id))
        _task_queue.put(lambda: self._send_track_check())

    def dispatch_track_data(self, track_data):
        log('[trackUploader] track data dispatched')
        _task_queue.put(lambda: self._send_track_data(track_data))

    def _send_track_check(self):
        log('[trackUploader] sending track check {}'.format(self.track_id))
        response_data = send_track_check({'trackId': self.track_id})
        log('[trackUploader] received track check: {}'.format(response_data))
        if self.check_callback:
            self.check_callback(response_data)
    
    def _send_track_data(self, track_data: dict):
        log('[trackUploader] sending track data {}: {}'.format(track_data['trackId'], track_data.keys()))
        success = send_track_data(track_data)
        log('[trackUploader] received track data: {}'.format(success))



class LapUploader:
    def __init__(self, session_data):
        self.session_data = session_data
        self.session_id = None
        self.session_lap_ids = []
        log("[lapUploader] Initialised")

    def reset(self, lap_count):
        log("[lapUploader] Clearing Session {}".format(self.session_id))
        for lap_id in self.session_lap_ids:
            log("[lapUploader] Lap {}".format(lap_id))
        _task_queue.put(lambda: self._close_session(lap_count, self.session_id))
        self.session_data = None
        self.session_id = None
        self.session_lap_ids = []

    def _upload_lap(self, lap_data={}, session_data={}):
        payload = dict(lap_data) if lap_data else {}
        if lap_data:
            payload["sessionData"] = session_data
            if self.session_id:
                payload["sessionId"] = self.session_id
        lap_id, session_id = handle_lap(payload)
        if lap_id:
            log('[lapUploader] received lap {} session {}'.format(lap_id, self.session_id))
            self.session_id = session_id
            self.session_lap_ids.append(lap_id)

    def dispatch_lap(self, lap_data):
        if lap_data:
            log("[lapUploader] lap dispatched: Session {}".format(self.session_id if self.session_id else "Unknown"))
        else:
            log("[lapUploader] Sending Session Handshake")
        ac.ext_perfBegin("pdata_lap_queue")
        _task_queue.put(lambda: self._upload_lap(lap_data, self.session_data))
        ac.ext_perfEnd("pdata_lap_queue")

    def _close_session(self, lap_count, session_id):
        if session_id:
            log("[lapUploader] Closing Session {}".format(session_id))
            close_session(session_id, lap_count)
        else:
            log('[lapUploader] No session to close')
        
