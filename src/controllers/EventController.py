from src.exceptions import SessionBoundaryExceeded
from src.controllers import SessionController
from src.plogging import pLogger

from src.worker import worker

from src.models import EventData, UpdatePayload

log = pLogger(__name__).log


class EventController:
    def __init__(self, event_data):
        # type: (EventData) -> None
        self.event_data = event_data
        self.session = None  # type: SessionController | None
        # TODO: Get track_id from TrackDataController so it's consistent
        log("Event Controller Ready")

    def update(self, payload):
        # type: (UpdatePayload) -> None
        """Take a full game tick bundle, and direct it towards the appropriate session"""

        if not self.session:
            # Create a new session with the provided data
            self.session = SessionController(self.event_data, payload.session)

        try:
            self.session.update(payload)
        except SessionBoundaryExceeded:
            # Old session can't handle the tick - close it, create a new one, and try the tick again
            self.session.close()
            self.session = SessionController(self.event_data, payload.session)
            self.session.update(payload)

    @property
    def track_length(self):
        return self.event_data.track_length

    def close(self):
        if self.session:
            self.session.close()
        worker.stop()
        log("Closed Event")
