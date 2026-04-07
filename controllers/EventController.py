from plogging import pLogger

log = pLogger(__name__).log


class EventController:
    def __init__(self, event_data):
        self.event_data = event_data
        log("Event Controller Setup Complete")