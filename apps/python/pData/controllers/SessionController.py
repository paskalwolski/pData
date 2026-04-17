from datetime import datetime

from controllers.LapController import LapController
from models import EventData, SessionData, UpdatePayload
from plogging import pLogger
from exceptions import LapBoundaryExceeded, SessionBoundaryExceeded

log = pLogger(__name__).log


class SessionController:
    def __init__(self, event_data, session_type):
        # type: (EventData, str) -> None
        self.session_data = SessionData(event_data, session_type, datetime.utcnow())
        self.laps = []
        log("Session Ready")

    def update(self, payload):
        # type: (UpdatePayload) -> None
        session = payload.session
        if session != self.session_data.session:
            raise SessionBoundaryExceeded()

        # TODO: Interact with LapController
        try:
            self.lap_controller.update(payload)
        except LapBoundaryExceeded:
            last_lap_time = payload.lap_data.last_lap_time
            self.lap_controller.close(last_lap_time)
            lap_number = payload.lap_data.lap_number
            self.lap_controller = LapController(self.session_data, lap_number)

    def close(self):
        log("Closing Session {}".format(self.session_data.session))
        # TODO: Check if we have valid laps, and decide to post the session
        return

    def register_lap(self, lap_id):
        # type: (str) -> None
        """Callback used when closing a lap
        this allows the session to keep track of how many laps were live
        """
        self.laps.append(lap_id)
