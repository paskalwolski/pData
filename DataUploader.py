import threading
from plogging import log
from ext_requests import handle_lap


class LapUploader:
    def __init__(self, session_data):
        self.session_data = session_data
        self.lap_entries = []

        log("[uploader] Initialised")

    def reset(self):
        self.session_data = None
        self.lap_entries = []

    def _upload_lap(self, lap_data):
        payload = dict(lap_data)
        payload['sessionData'] = self.session_data
        log("[request] POST lap: lap={}".format(payload.get('lapNumber')))
        handle_lap(payload)
        log("[request] lap sent: lap={}".format(payload.get('lapNumber')))

    def dispatch_lap(self, lap_data):
        log("[uploader] lap {} dispatched".format(lap_data.get('lapNumber')))
        lap_thread = threading.Thread(name='pdata_uploader_lap', target=self._upload_lap, args=(lap_data,), daemon=True)
        lap_thread.start()
