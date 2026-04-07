from datetime import datetime

from plogging import pLogger
from exceptions import SessionBoundaryExceeded

log = pLogger(__name__).log


class SessionController:
    def __init__(self, event_data, session_type):
        # type: (dict, str) -> None
        self.session_type = session_type
        self.session_data = SessionController.get_session_data(session_type, event_data)
        self.session_timestamp = datetime.now(datetime.UTC)
        self.laps = []
        log("Session Ready")

    def handle_tick(self, payload):
        # type: (dict) -> None
        session_type = payload.pop("session_type")
        if session_type != self.session_type:
            raise SessionBoundaryExceeded()

        # TODO: Interact with LapController
        # self.lap_controller.handle_tick(payload)
    

    def close(self):
        log("Closing Session {}".format(self.session_type))
        return
    
    def register_lap(self, lap_id):
        # type: (str) -> None
        """Callback used when closing a lap - this allows the session to keep track of how many laps were live"""
        self.laps.append(lap_id)
    
    @staticmethod
    def get_session_data(session_type, event_data):
        # type: (str, dict) -> dict
        _data_fields = ('driver', 'car', 'track')
        session_data = {k: event_data.get(k, None) for k in _data_fields}
        session_data['sessionType'] = session_type
        return session_data
