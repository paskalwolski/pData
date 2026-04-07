from exceptions import InvalidBundle, SessionBoundaryExceeded
from controllers.SessionController import SessionController
from plogging import pLogger

log = pLogger(__name__).log


class EventController:
    def __init__(self, event_data, session_type):
        self.event_data = event_data
        # TODO: Get track_id from TrackDataController so it's consistent
        self.session_controller = SessionController(event_data, session_type)
        log("Event Controller Ready")

    def handle_tick(self, payload):
        # type: (dict) -> None
        """Take a full game tick bundle, and direct it towards the appropriate session"""

        session_type = payload.get('session_type', None)
        if not session_type:
            raise InvalidBundle("No 'session_type' found")

        try:
            self.session_controller.handle_tick(payload)
        except SessionBoundaryExceeded:
            # Old session can't handle the tick - close it, create a new one, and try the tick again
            self.session_controller.close()
            self.session_controller = SessionController(self.event_data, session_type)
            self.session_controller.handle_tick(payload)

    def close(self):
        self.session_controller.close()
        log('Closing Event')
        return
