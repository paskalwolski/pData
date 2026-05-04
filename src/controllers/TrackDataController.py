import configparser
import json
import os
import traceback

from src.models import MapConfigData, TrackConfigData
from src.plogging import pLogger

# TODO: Add Track Data Display

log = pLogger(__name__).log


class TrackDataController:
    def __init__(self, track, variant):
        # type: (str, str | None) -> None
        self.track = track
        self.variant = variant
        self.root_track_dir = os.path.join(os.getcwd(), "content", "tracks", self.track)

        self.track_details = None  # type: TrackConfigData | None
        self.map_details = None  # type: MapConfigData | None

        self._load_track_details()
        self._load_map_details()
        # TODO: Add Section Data
        # TODO: Expose data states to see if they're suitable for upload

    @property
    def track_id(self):
        return "{}_{}".format(self.track, self.variant) if self.variant else self.track

    def _load_track_details(self):
        track_ui_path = (
            os.path.join(self.root_track_dir, "ui")
            if not self.track
            else os.path.join(self.root_track_dir, "ui", self.track)
        )
        ui_ini_path = os.path.join(track_ui_path, "ui_track.json")
        try:
            with open(ui_ini_path, "r", encoding="utf-8") as ui_file:
                data = ui_file.read()
                track_details = json.loads(data)
                self.track_details = TrackConfigData(track_name=track_details["name"])
        except (FileNotFoundError, json.JSONDecodeError):
            log("Unable to read Track Details", traceback.format_exc())

    def _load_map_details(self):
        try:
            track_dir = (
                os.path.join(self.root_track_dir, self.track)
                if self.track
                else self.root_track_dir
            )
            map_ini_path = os.path.join(track_dir, "data", "map.ini")
            cp = configparser.ConfigParser()
            cp.read(map_ini_path)
            track_params = cp["PARAMETERS"]
            height = float(track_params["HEIGHT"])
            width = float(track_params["WIDTH"])
            x_offset = float(track_params["X_OFFSET"])
            y_offset = float(track_params["Z_OFFSET"])
            margin = float(track_params["MARGIN"])

            track_image_path = os.path.join(track_dir, "map.png")

            self.map_details = MapConfigData(
                height, width, x_offset, y_offset, margin, track_image_path
            )
        except (configparser.ParsingError, KeyError, FileNotFoundError):
            log("Unable to read map data", traceback.format_exc())
