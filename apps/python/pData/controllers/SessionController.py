from datetime import datetime

from worker import worker
from controllers import LapController
from models import EventData, SessionData, UpdatePayload
from plogging import pLogger
from exceptions import LapBoundaryExceeded, SessionBoundaryExceeded

logger = pLogger(__name__)


class SessionController:
    def __init__(self, event_data, session_type):
        # type: (EventData, str) -> None
        self.event_data = event_data
        self.session = session_type
        self.session_timestamp = datetime.utcnow()
        self.remote_session_id = None
        self.laps = []  # type: list[str]
        self.lap = None  # type: LapController | None
        logger.log("Session Ready")

    def update(self, payload):
        # type: (UpdatePayload) -> None
        if not self.lap:
            self.lap = LapController(
                self.session_data, payload.lap_data.lap_number, self.register_lap
            )

        # Check session boundary
        if payload.session != self.session:
            raise SessionBoundaryExceeded()

        try:
            self.lap.update(payload)
        except LapBoundaryExceeded:
            last_lap_time = payload.lap_data.last_lap_time
            self.lap.close(last_lap_time)
            lap_number = payload.lap_data.lap_number
            self.lap = LapController(self.session_data, lap_number, self.register_lap)

    def close(self):
        # TODO: Check if we have valid laps, and decide to post the session
        if self.lap:
            self.lap.close()
        worker.enqueue(self._close_process)
        logger.log("Fired Close {} Session".format(self.session))

    def register_lap(self, lap_id, session_id):
        # type: (str, str | None) -> None
        """Callback used when closing a lap
        this allows the session to keep track of how many laps were live
        """
        if not self.remote_session_id and session_id:
            self.remote_session_id = session_id
        self.laps.append(lap_id)

    @property
    def session_data(self):
        return SessionData(self.event_data, self.session, self.session_timestamp)

    def _close_process(self):
        # type: () -> None
        """
        Relies on the lap close being ahead of this in the queue
        so the lap will be registered and taken into account
        """
        if self.remote_session_id:
            logger.worker_log(
                "Closing Remote Session {}".format(self.remote_session_id)
            )
