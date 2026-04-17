from exceptions import InvalidBundle, LapBoundaryExceeded, SessionBoundaryExceeded
from plogging import pLogger

from models import UpdatePayload, SessionData

log = pLogger(__name__).log


class LapController:
    def __init__(self, session_data, lap_number):
        # type: (SessionData, int) -> None
        self.session_data = session_data
        self.lap_number = lap_number
        self.lap_data = []
        log("Lap {} Ready".format(lap_number))

    def update(self, payload):
        # type: (UpdatePayload) -> None | int
        lap = payload.lap_data.lap_number
        if not lap:
            raise InvalidBundle()
        if lap != self.lap_number:
            if lap == 1:
                # Reset lap count implies a new session
                # TODO: Handle the case where current_lap == new_lap == 1 (restart on lap 1)
                raise SessionBoundaryExceeded(reason="Lap Count Reset")

            # Next lap started
            raise LapBoundaryExceeded(
                reason="Lap Number {} does not match expected {}".format(
                    lap, self.lap_number
                ),
            )

    def close(self, last_lap_time=None):
        # type: (float | None) -> None
        if not last_lap_time:
            log("Discarded lap {} - No Lap Time".format(self.lap_number))
        else:
            log("Closed Lap {}: {}".format(self.lap_number, last_lap_time))
            # TODO: Post the lap
