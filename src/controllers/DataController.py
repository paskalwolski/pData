from src.controllers import TrackDataController
from src.data_displays.DataControllerDisplay import DataControllerDisplay

class TrackIdData:
    def __init__(self, track, variant, length):
        # type: (str, str | None, float) -> None
        self.track = track
        self.variant = variant
        self.length = length

class DataController:
    def __init__(self, track_data):
        # type: (TrackIdData) -> None
        display = DataControllerDisplay(lambda: self.track_data_controller.fire_track_data_upload())
        self.track_data_controller = TrackDataController(track_data.track, track_data.variant, track_data.length, display)

    @property
    def track_id(self):
        return self.track_data_controller.track_id