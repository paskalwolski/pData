from exceptions import InvalidBundle, SessionBoundaryExceeded
from controllers.SessionController import SessionController
from plogging import pLogger

from models import EventData, UpdatePayload

log = pLogger(__name__).log


class EventController:
    """
    Singleton class for the current AC Game Instance.
    Recreated only when the game is restarted
    """

    def __init__(self, event_data):
        # type: (EventData) -> None
        self.event_data = event_data
        # TODO: Get track_id from TrackDataController so it's consistent
        log("Event Controller Ready")

    def update(self, payload):
        # type: (UpdatePayload) -> None
        """Take a full game tick bundle, and direct it towards the appropriate session"""

        session = payload.session
        if not session:
            raise InvalidBundle("No 'session_type' found")

        try:
            self.session_controller.update(payload)
        except SessionBoundaryExceeded:
            # Old session can't handle the tick - close it, create a new one, and try the tick again
            self.session_controller.close()
            self.session_controller = SessionController(self.event_data, session)
            self.session_controller.update(payload)

    def close(self):
        self.session_controller.close()
        log("Closing Event")
        return
