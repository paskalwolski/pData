import threading
import ac
from plogging import log
from ext_requests import create_session, handle_lap


class SESSION_STATE:
    inactive = "INACTIVE"
    pending = "PENDING"
    ready = "READY"

class LapUploader:
    def __init__(self, session_data):
        self.session_data = session_data
        self.session_state = SESSION_STATE.inactive
        self.session_id = None
        self.lap_entries = []

        log("[uploader] Initialised")

    def reset(self):
        self.session_data = None
        self.session_state = SESSION_STATE.inactive
        self.session_id = None
        self.lap_entries = []

    def _upload_session(self, session_data):
        log("[request] POST session: {}".format(session_data.get('sessionType')))
        self.session_id = create_session(session_data)
        log("[request] session created: id={}".format(self.session_id))

    def _upload_lap(self, lap_data):
        payload = dict(lap_data)
        payload['sessionId'] = self.session_id
        log("[request] POST lap: session={} lap={}".format(self.session_id, payload.get('lap_number')))
        handle_lap(payload)
        log("[request] lap sent: session={} lap={}".format(self.session_id, payload.get('lap_number')))

    def _trigger_upload(self):
        if not self.session_id and self.session_state == SESSION_STATE.inactive:
            self.session_state = SESSION_STATE.pending
            session_thread = threading.Thread(name='pdata_uploader_session', target=self._upload_session, args=(self.session_data,), daemon=True)
            session_thread.start()
            # Forcibly wait with this thread until it's complete
            session_thread.join()
            self.session_state = SESSION_STATE.ready
        if not self.session_state == SESSION_STATE.ready:
            # Session upload failed or still pending - retry
            self.dispatch()
            return
        # TODO: Improve this sequencing so that we always target the given lap instead of [0]
        lap_thread = threading.Thread(name='pdata_uploader_lap', target=self._upload_lap, args=(self.lap_entries.pop(0),), daemon=True)
        lap_thread.start()

    def dispatch_lap(self, lap_data):
        log("[uploader] lap {} queued ({} in queue)".format(lap_data.get('lap_number'), len(self.lap_entries) + 1))
        self.lap_entries.append(lap_data)
        self.dispatch()

    def dispatch(self):
        ac.ext_perfBegin("pdata_thread_start")
        control_thread = threading.Thread(name='pdata_uploader_control', target=self._trigger_upload, daemon=True)
        control_thread.start()
        ac.ext_perfEnd("pdata_thread_start")
