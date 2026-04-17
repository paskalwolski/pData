from datetime import datetime

from controllers.LapController import LapController
from models import EventData, SessionData, UpdatePayload
from plogging import pLogger
from exceptions import LapBoundaryExceeded, SessionBoundaryExceeded

log = pLogger(__name__).log


class SessionController:
    def __init__(self, event_data, session_type):
        # type: (EventData, str) -> None
        self.event_data = event_data
        self.session = session_type
        self.session_timestamp = datetime.utcnow()
        self.laps = []  # type: list[str]
        self.lap = None  # type: LapController | None
        log("Session Ready")

    def update(self, payload):
        # type: (UpdatePayload) -> None
        if not self.lap:
            self.lap = LapController(self.session_data, payload.lap_data.lap_number)

        # Check session boundary
        if payload.session != self.session:
            raise SessionBoundaryExceeded()

        try:
            self.lap.update(payload)
        except LapBoundaryExceeded:
            last_lap_time = payload.lap_data.last_lap_time
            self.lap.close(last_lap_time)
            lap_number = payload.lap_data.lap_number
            self.lap = LapController(self.session_data, lap_number)

    def close(self):
        # TODO: Check if we have valid laps, and decide to post the session
        if self.lap:
            self.lap.close()
        log("Closed Session {}".format(self.session))

    def register_lap(self, lap_id):
        # type: (str) -> None
        """Callback used when closing a lap
        this allows the session to keep track of how many laps were live
        """
        self.laps.append(lap_id)

    @property
    def session_data(self):
        return SessionData(self.event_data, self.session, self.session_timestamp)
