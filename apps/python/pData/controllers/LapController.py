from exceptions import InvalidBundle, LapBoundaryExceeded
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
        return

    def update(self, payload):
        # type: (UpdatePayload) -> None | int
        lap = payload.lap_data.lap_number
        if not lap:
            raise InvalidBundle()
        if lap != self.lap_number:
            # Mark the last meter of the lap - as this might not correspond to track_length
            raise LapBoundaryExceeded(
                reason="Lap Number {} does not match expected {}".format(
                    lap, self.lap_number
                ),
            )

    def close(self, last_lap_time):
        # type: (float | None) -> None
        if not last_lap_time:
            log("No lap time provided - discarding lap {}".format(self.lap_number))
        # TODO: Post the lap
