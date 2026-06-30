import traceback
from datetime import datetime

from src.worker import worker
from src.controllers.LapController import LapController
from src.models import EventData, SessionData, UpdateData, CreateSessionPayload
from src.plogging import pLogger
from src.exceptions import LapBoundaryExceeded, SessionBoundaryExceeded, APIException
from src.data_displays.LapStatus import lap_status_display

import src.api_client as api_client

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
        worker.enqueue(self._open_process)
        lap_status_display.register_session()
        logger.log("Session Ready")

    def update(self, payload):
        # type: (UpdateData) -> None
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
            try:
                self.lap.update(payload)
            except LapBoundaryExceeded:
                logger.log("Payload for lap {} unsuccessful".format(payload.lap_data.lap_number))
                return

    def close(self):
        if self.lap:
            self.lap.close()
        # worker.enqueue(self._close_process)
        logger.log("Fired Close {} Session".format(self.session))

    def register_lap(self, lap_id):
        # type: (str) -> None
        """Callback used when closing a valid lap.
        Tracks lap in session's lap list.
        """
        self.laps.append(lap_id)
        logger.log("Registered lap {} in session {}".format(lap_id, self.remote_session_id))

    @property
    def session_data(self):
        return SessionData(
            self.event_data,
            self.session,
            self.session_timestamp,
            self.remote_session_id,
        )

    def _close_process(self):
        # type: () -> None
        """
        Relies on the lap close being ahead of this in the queue
        so the lap will be registered and taken into account
        """
        if not self.remote_session_id:
            logger.worker_log("No remote session to close")
            return
        api_client.close_session({"sessionId": self.remote_session_id})
        logger.worker_log(
            "Closed Remote Session {}: {} laps".format(
                self.remote_session_id, len(self.laps)
            )
        )

    def _open_process(self):
        try:
            session_payload = CreateSessionPayload(self.session_data)
            session_id = api_client.create_session(session_payload)
            self.remote_session_id = session_id
            if self.lap:
                self.lap.register_session_id(session_id)
            logger.worker_log("Session created: {}".format(session_id))
            api_client.init_lap_handler()
        except APIException:
            logger.worker_log("Failed to create session", traceback.format_exc())
