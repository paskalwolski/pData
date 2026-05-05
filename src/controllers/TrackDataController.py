import base64
import configparser
import json
import math
import os
import traceback

from src import api_client
from src.exceptions import APIException
from src.worker import worker
from src.models import MapConfigData, TrackConfigData, TrackRequest, TrackDataState
from src.plogging import pLogger
from src.data_displays.TrackDataDisplay import TrackDataDisplay

log = pLogger(__name__).log


class TrackDataController:
    def __init__(self, track, variant):
        # type: (str, str | None) -> None
        self.display = TrackDataDisplay(self.fire_track_data_upload)
        self.track = track
        self.variant = variant
        
        self.root_track_dir = os.path.join(os.getcwd(), "content", "tracks", self.track)
        self.variant_dir = "layout_{}".format(self.variant) if self.variant and self.variant.startswith('ks_') else self.variant

        self.track_details = None  # type: TrackConfigData | None
        self.map_details = None  # type: MapConfigData | None

        self._load_track_details()
        self._load_map_details()
        # TODO: Add Section Data
        self.display.set_state(self.local_state)


    @property
    def track_id(self):
        return "{}_{}".format(self.track, self.variant) if self.variant else self.track


    def fire_track_data_upload(self):
        if not self.local_state.ready:
            log("Unable to upload Track data: Missing Data")
            return
        worker.enqueue(self._upload_track_data)
        log("Fired Track Data Upload: {}".format(self.track_id))

    def _load_track_details(self):
        track_ui_path = (
            os.path.join(self.root_track_dir, "ui")
            if not self.variant_dir
            else os.path.join(self.root_track_dir, "ui", self.variant_dir)
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
                os.path.join(self.root_track_dir, self.variant_dir)
                if self.variant_dir
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

    def _process_map_image(self):
        # type: () -> str | None
        """Return the Map Image as a B64 encoded string, if it exists"""
        image_path = getattr(self.map_details, "image_path", None)
        if not image_path:
            return None

        with open(image_path, "rb") as f:
            image_bytes = f.read()
        return base64.b64encode(image_bytes).decode("utf-8")

    def _upload_track_data(self):
        self.display.set_uploading()
        payload = TrackRequest(
            self.track_id,
            self.track_details,
            self.map_details,
            self._process_map_image(),
        )
        try:
            api_client.post_track_data(payload)
        except APIException as e:
            log("Failed Track Data Upload", traceback.format_exception(e))
            self.display.set_error()
            return
        log("Completed Track Data Upload: {}".format(self.track_id))
        self.display.set_complete()

    @property
    def local_state(self):
        # type: () -> TrackDataState
        has_track_details = bool(self.track_details)
        has_map_details = bool(self.map_details)
        map_margin_ok = self.map_details and math.floor(self.map_details.margin) == 10
        has_map = self.map_details and self.map_details.image_path
        return TrackDataState(has_track_details=has_track_details,has_map_details=has_map_details,map_margin_ok=map_margin_ok, has_map=has_map)