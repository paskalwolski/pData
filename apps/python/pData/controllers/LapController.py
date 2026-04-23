import traceback

from plogging import pLogger
from models import Telemetry, UpdatePayload, SessionData
from worker import worker
from exceptions import (
    APIException,
    InvalidBundle,
    LapBoundaryExceeded,
    SessionBoundaryExceeded,
)

from apps.python.pData import api_client


log = pLogger(__name__).log


class LapController:
    def __init__(self, session_data, lap_number, register_lap_callback):
        # type: (SessionData, int, callable) -> None  # type: ignore
        self.session_data = session_data
        self.lap_number = lap_number
        self.lap_telemetry = [
            None for _ in range(session_data.event_data.track_length)
        ]  # type: list[None | Telemetry]
        self.register_lap_with_session = register_lap_callback
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
            return
        worker.enqueue(lambda: self._process(last_lap_time))
        log("Fired Lap {}: {}".format(self.lap_number, last_lap_time))

    def _process(self, last_lap_time):
        # type: (float) -> None
        telemetry_object = self._prepare_telemetry_data()  # pylint: disable=W0612
        lap_data = {
            "lapNumber": self.lap_number,
            "lapTime": last_lap_time,
            # TODO: Fix valid and pit values
            "isValid": True,
            "isPit": True,
            "lapData": telemetry_object,
        }
        try:
            lap_id, session_id = api_client.post_lap(lap_data)
        except APIException as e:
            log("Failed Lap Upload", traceback.format_exception(e))
            return
        # TODO: Register response with SessionController
        self.register_lap_with_session(lap_id, session_id)
        log("Processed Lap {}: {}".format(self.lap_number, last_lap_time))

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
