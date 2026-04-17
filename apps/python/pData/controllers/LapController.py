from exceptions import InvalidBundle, LapBoundaryExceeded, SessionBoundaryExceeded
from plogging import pLogger

from models import Telemetry, UpdatePayload, SessionData

log = pLogger(__name__).log


class LapController:
    def __init__(self, session_data, lap_number):
        # type: (SessionData, int) -> None
        self.session_data = session_data
        self.lap_number = lap_number
        self.lap_telemetry = [
            None for _ in range(session_data.event_data.track_length)
        ]  # type: list[None | Telemetry]
        self.last_stored_meter = 0
        log("Lap {} Ready".format(lap_number))

    def update(self, payload):
        # type: (UpdatePayload) -> None
        self._check_lap_boundary(payload)

        # Track this telemetry point
        telemetry = payload.lap_data.telemetry
        self.last_stored_meter = telemetry.d
        self.lap_telemetry[telemetry.d] = telemetry

    def close(self, last_lap_time=None):
        # type: (float | None) -> None
        if not last_lap_time:
            log("Discarded lap {} - No Lap Time".format(self.lap_number))
        else:
            telemetry_payload = self._prepare_telemetry_data()  # pylint: disable=W0612
            # TODO: Post the lap
            log("Closed Lap {}: {}".format(self.lap_number, last_lap_time))

    def _check_lap_boundary(self, payload):
        # type: (UpdatePayload) -> None
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

    def _prepare_telemetry_data(self):
        # type: () -> dict
        # Adjust the telemetry for last meter value
        shifted_telemetry = (
            self.lap_telemetry[self.last_stored_meter :]
            + self.lap_telemetry[: self.last_stored_meter]
        )
        telemetry_object = Telemetry.get_telemetry_object(  # pylint: disable=W0612
            shifted_telemetry
        )
        return telemetry_object
