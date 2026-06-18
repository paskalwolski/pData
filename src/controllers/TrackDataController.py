import base64
import configparser
import json
import math
import os
import traceback

from src import api_client
from src.exceptions import APIException
from src.worker import worker
from src.models import (
    MapConfigData,
    RequestTrackPayload,
    TrackConfigData,
    TrackDataFieldPayload,
    TrackPayload,
    TrackDataState,
    TrackSectionData,
)
from src.plogging import pLogger

log = pLogger(__name__).log

_ROW_DEFS = [
    (TrackDataState.track_details_id, "Track Details",    True),
    (TrackDataState.map_details_id,   "Map Details",      True),
    (TrackDataState.map_present_id,   "Map Image",        True),
    (TrackDataState.map_margin_id,    "Margin (10px)",    True),
    (TrackDataState.section_data_id,  "Track Sections", False),
]


class TrackDataController:
    def __init__(self, track, variant, track_length, display):
        self.display = display
        self.track = track
        self.variant = variant
        self.track_length = track_length

        self.root_track_dir = os.path.join(os.getcwd(), "content", "tracks", self.track)

        self.track_details = None  # type: TrackConfigData | None
        self.map_details = None  # type: MapConfigData | None
  
        for key, label, required in _ROW_DEFS:
            if required:
                self.display.register_required_row(key, label)
            else:
                self.display.register_optional_row(key, label)
        self.display.build()

        self.fire_get_track_data()
        try:
            self._load_track_details()
            self._load_map_details()
            self._load_section_details()

            log(self.section_data)
        except Exception:  # pylint: disable=W0718
            log("Error initing Track Details", traceback.format_exc())

        self.display.set_values(1, dict(self.local_state.items()))

    @property
    def track_id(self):
        return "{}_{}".format(self.track, self.variant) if self.variant else self.track

    def fire_track_data_upload(self):
        state_values = dict(self.local_state.items())
        if not all(state_values.get(key) for key, _, required in _ROW_DEFS if required):
            log("Unable to upload Track data: Missing Data")
            return
        worker.enqueue(self._upload_track_data_process)
        log("Fired Track Data Upload: {}".format(self.track_id))

    def fire_get_track_data(self):
        worker.enqueue(self._get_track_data_process)
        log("Fired Track Data Fetch: {}".format(self.track_id))

    def _load_track_details(self):
        track_ui_path = (
            os.path.join(self.root_track_dir, "ui", self.variant)
            if self.variant
            else os.path.join(self.root_track_dir, "ui")
        )
        ui_ini_path = os.path.join(track_ui_path, "ui_track.json")
        try:
            with open(ui_ini_path, "r", encoding="utf-8") as ui_file:
                data = ui_file.read()
                track_details = json.loads(data)
                self.track_details = TrackConfigData(track_name=track_details["name"], track_length=self.track_length)
        except (FileNotFoundError, json.JSONDecodeError):
            log("Unable to read Track Details", traceback.format_exc())

    def _load_map_details(self):
        try:
            track_dir = (
                os.path.join(self.root_track_dir, self.variant)
                if self.variant
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

    def _load_section_details(self):
        try:
            section_file_path = os.path.join(self.track_dir, 'data', 'sections.ini')
            cp = configparser.ConfigParser()
            try:
                cp.read(section_file_path)
            except (configparser.Error, FileNotFoundError):
                log("Track does not have section data")
                self.section_data = []
                return
            sections = []
            for section in cp.sections():
                section_data = cp[section]
                section_details = TrackSectionData(
                    section_data['TEXT'],
                    int(math.ceil(float(section_data['IN']) * self.track_length)),
                    int(math.ceil(float(section_data['OUT']) * self.track_length)),
                )
                sections.append(section_details)
            self.section_data = sections
        except Exception as e:
            log('Unable to read section data', traceback.format_exc())
            self.section_data = []

    def _prepare_map_image(self):
        # type: () -> str | None
        """Return the Map Image as a B64 encoded string, if it exists"""
        image_path = getattr(self.map_details, "image_path", None)
        if not image_path:
            return None

        with open(image_path, "rb") as f:
            image_bytes = f.read()
        return base64.b64encode(image_bytes).decode("utf-8")

    def _upload_track_data_process(self):
        self.display.set_uploading()
        payload = TrackPayload(
            self.track_id,
            self.track_details,
            self.map_details,
            self._prepare_map_image(),
        )
        try:
            api_client.post_track_data(payload)
        except APIException:
            log("Failed Track Data Upload", traceback.format_exc())
            self.display.set_error()
            return
        log("Completed Track Data Upload: {}".format(self.track_id))
        self.display.set_complete()

    def _get_track_data_process(self):
        payload = RequestTrackPayload(self.track_id)
        try:
            remote_data = api_client.check_track_data(payload)
            remote_track_state = (
                remote_data.track_data.as_state()
                if remote_data.exists
                else TrackDataState.empty()
            )
            self.display.set_values(2, dict(remote_track_state.items()))
        except APIException:
            log("Failed to get Track Data from Remote", traceback.format_exc())
            self.display.set_values(2, dict(TrackDataState.empty().items()))

    @property
    def local_state(self):
        # type: () -> TrackDataState
        return TrackDataFieldPayload(
            self.track_details, self.map_details, self._prepare_map_image(), self.section_data
        ).as_state()
    
    @property
    def track_dir(self):
        return (
            os.path.join(
                self.root_track_dir, self.variant
            ) 
            if self.variant 
            else self.root_track_dir
        )
