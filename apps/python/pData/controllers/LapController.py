from exceptions import InvalidBundle, LapBoundaryExceeded
from plogging import pLogger

log = pLogger.log(__name__)

class LapController:
    def __init__(self, seession_data, lap_number):
        self.session_data = self.session_data
        self.lap_number = lap_number

    def handle_tick(self, payload):
        # type: (dict) -> None
        lap_number = payload.get("lap_number", None)
        if not lap_number:
            raise InvalidBundle()
        if lap_number != self.lap_number:
            raise LapBoundaryExceeded()
        
    def close(self):
        log("Closing Lap {}".format(self.lap_number))