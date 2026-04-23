import traceback

from plogging import pLogger
from models import LapPayload, Telemetry, UpdatePayload, SessionData
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

        self.is_pit = False
        self.is_invalid = False

        log("Lap {} Ready".format(lap_number))

    def update(self, payload):
        # type: (UpdatePayload) -> None
        self._check_lap_boundary(payload.lap_data)
        self._check_for_discard(payload.lap_data)
        # Track this telemetry point
        telemetry = payload.lap_data.telemetry
        self.last_stored_meter = telemetry.d
        self.lap_telemetry[telemetry.d] = telemetry

    def close(self, last_lap_time=None):
        # type: (float | None) -> None
        if not last_lap_time:
            log("Discarded lap {} - No Lap Time".format(self.lap_number))
            return
        worker.enqueue(lambda: self._close_process(last_lap_time))
        log("Fired Close Lap {}: {}".format(self.lap_number, last_lap_time))

    def _close_process(self, last_lap_time):
        # type: (float) -> None
        telemetry_object = (
            None if self.discard else self._prepare_telemetry_data()
        )  # pylint: disable=W0612
        lap_data = {
            "lapNumber": self.lap_number,
            "lapTime": last_lap_time,
            "isValid": not self.is_invalid,
            "isPit": self.is_pit,
            "discard": self.discard,
            "lapData": telemetry_object,
        }
        try:
            lap_id, session_id = api_client.post_lap(lap_data)
        except APIException as e:
            log("Failed Lap Upload", traceback.format_exception(e))
            return
        if not self.discard:
            self.register_lap_with_session(lap_id, session_id)
        log("Processed Lap {}: {}".format(self.lap_number, last_lap_time))

    def _check_lap_boundary(self, lap_data):
        # type: (LapPayload) -> None
        lap = lap_data.lap_number
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

    def _check_for_discard(self, lap_data):
        # type: (LapPayload) -> None
        if lap_data.in_pit:
            self.is_pit = True
        if lap_data.invalid:
            self.is_invalid = True

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

    @property
    def discard(self):
        # type: () -> bool
        # TODO: Improve discard logic eg. T if practice, F if race
        return self.is_invalid or self.is_pit
