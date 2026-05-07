from datetime import datetime
import json
import math

# pylint: disable=line-too-long,R0902,R0913
# pylint: disable=R0913


class BaseRequestPayload:
    """
    ABC that is used for data structures in outgoing requests which
    provides serialisation logic for camelCase network structures
    """

    _json_field_names = {}

    def to_json_dict(self):
        d = {}
        for f, j in self._json_field_names.items():
            v = getattr(self, f, None)
            if v is not None:
                d[j] = v.to_json_dict() if isinstance(v, BaseRequestPayload) else v
        return d

    def to_json(self):
        return json.dumps(self.to_json_dict())

    def __getitem__(self, key):
        return getattr(self, key, None)

    @classmethod
    def from_json_dict(cls, json_dict, overrides=None):
        effective_json_field_names = dict(cls._json_field_names)
        if overrides:
            effective_json_field_names.update(overrides)
        instance = cls.__new__(cls)
        for k, v in effective_json_field_names.items():
            setattr(instance, k, json_dict.get(v) if json_dict else None)
        return instance


# Telemetry: Static bundle containing the telemtry data for a single meter
class Telemetry:
    _json_field_names = {
        "speed": "speed",
        "lap_time": "lapTime",
        "gas": "gas",
        "brake": "brake",
        "gear": "gear",
        "steer": "steer",
        "rpm": "rpm",
        "pos_x": "posX",
        "pos_z": "posZ",
        "ers": "ers",
    }

    def __init__(
        self, *, d, lap_time, speed, gas, brake, gear, steer, rpm, pos_x, pos_z, ers
    ):
        # type: (Telemetry, int, float, float, float, float, int, float, float, float, float, float) -> None
        self.d = d
        self.lap_time = lap_time
        self.speed = speed
        self.gas = gas
        self.brake = brake
        self.gear = gear
        self.steer = steer
        self.rpm = rpm
        self.pos_x = pos_x
        self.pos_z = pos_z
        self.ers = ers

    @staticmethod
    def serialise_telemetry_object(telemetry):
        # type: (list[Telemetry | None]) -> dict
        """
        Prepare a json-friendly dict to store separate telemetry arrays.

        This splits the stored array-of-objects into an object of arrays
        reducing outgoing bundle size and allowing data to be directly
        stored in DB without further processing
        """
        telemetry_object = {j: [] for j in Telemetry._json_field_names.values()}
        for t in telemetry:
            for f, j in Telemetry._json_field_names.items():
                telemetry_object[j].append(getattr(t, f, None) if t else None)
        return telemetry_object


class SessionData(BaseRequestPayload):
    _json_field_names = {"event_data"}

    def __init__(self, event_data, session, session_timestamp, remote_session_id):
        # type: (EventData, str, datetime, str | None) -> None
        self.event_data = event_data
        self.session = session
        self.session_timestamp = session_timestamp
        self.remote_session_id = remote_session_id


class LapData:
    def __init__(self, *, lap_number, telemetry, invalid, in_pit, last_lap_time=None):
        # type: (LapData, int, Telemetry, bool, bool, float | None) -> None
        self.lap_number = lap_number
        self.telemetry = telemetry

        self.invalid = invalid
        self.in_pit = in_pit
        self.last_lap_time = last_lap_time


class UpdateData:
    def __init__(self, session, lap_data):
        # type: (UpdateData, str, LapData) -> None
        self.session = session
        self.lap_data = lap_data


class EventData:
    def __init__(self, driver, track, car, track_length):
        # type: (str, str, str, int) -> None
        self.driver = driver
        self.track = track
        self.track_length = track_length
        self.car = car


class SessionPayload(BaseRequestPayload):
    _json_field_names = {
        "driver": "driver",
        "car": "car",
        "track": "track",
        "session_time": "sessionTime",
        "session_type": "sessionType",
    }

    def __init__(self, sessionData):
        # type: (SessionData) -> None
        self.driver = sessionData.event_data.driver
        self.car = sessionData.event_data.car
        self.track = sessionData.event_data.track
        self.session_time = sessionData.session_timestamp.isoformat()
        self.session_type = sessionData.session


class LapPayload(BaseRequestPayload):
    _json_field_names = {
        "lap_number": "lapNumber",
        "lap_time": "lapTime",
        "is_valid": "isValid",
        "is_pit": "isPit",
        "discard": "discard",
        "lap_data": "lapData",
        "session_data": "sessionData",
        "session_id": "sessionId",
    }

    def __init__(
        self, lap_number, lap_time, is_valid, is_pit, discard, lap_data, session_data
    ):
        # type: (int, float, bool, bool, bool, dict[str, list] | None, SessionData) -> None
        self.session_id = session_data.remote_session_id
        self.lap_number = lap_number
        self.lap_time = lap_time
        self.is_valid = is_valid
        self.is_pit = is_pit
        self.discard = discard
        self.lap_data = lap_data
        self.session_data = SessionPayload(session_data)


class TrackDataState:
    track_details_id = "track_details"
    map_details_id = "map_details"
    map_present_id = "map_present"
    map_margin_id = "map_margin_ok"

    value_ids = [track_details_id, map_details_id, map_present_id, map_margin_id]

    value_labels = {
        track_details_id: "Track Details",
        map_details_id: "Map Details",
        map_present_id: "Map Image",
        map_margin_id: "Margin (10px)",
    }

    def __init__(
        self,
        *,
        has_track_details=None,
        has_map_details=None,
        map_margin_ok=None,
        has_map=None
    ):
        setattr(self, self.track_details_id, has_track_details)
        setattr(self, self.map_details_id, has_map_details)
        setattr(self, self.map_present_id, has_map)
        setattr(self, self.map_margin_id, map_margin_ok)

    def items(self):
        return {id: getattr(self, id, None) for id in TrackDataState.value_ids}.items()  # type: ignore

    @property
    def ready(self):
        for value_id in self.value_ids:
            if not getattr(self, value_id, None):
                return False
        return True

    @classmethod
    def empty(cls):
        return TrackDataState(
            has_track_details=False,
            has_map_details=False,
            map_margin_ok=False,
            has_map=False,
        )


class TrackConfigData:
    """Data grabbed from the Track config file"""

    def __init__(self, track_name):
        # type: (str | None) -> None
        self.track_name = track_name


class MapConfigData:
    def __init__(self, height, width, x_offset, y_offset, margin, image_path):
        # type: (float, float, float, float, float, str) -> None
        self.height = height
        self.width = width
        self.x_offset = x_offset
        self.y_offset = y_offset
        self.margin = margin
        self.image_path = image_path


class TrackPayload(BaseRequestPayload):
    _json_field_names = {
        "track_id": "trackId",
        "track_data": "trackData",
    }

    def __init__(self, track_id, track_details, map_details, map_image_data=None):
        # type: (str, TrackConfigData | None, MapConfigData | None, str | None) -> None
        self.track_id = track_id
        self.track_data = TrackDataPayload(track_details, map_details, map_image_data)


class TrackDataPayload(BaseRequestPayload):
    _json_field_names = {
        "track_name": "trackName",
        "width": "width",
        "height": "height",
        "x_offset": "xOffset",
        "y_offset": "yOffset",
        "margin": "margin",
        "image": "image",
    }

    def __init__(self, track_details, map_details, map_image_data):
        # type: (TrackConfigData | None, MapConfigData | None, str | None) -> None
        if track_details:
            self.track_name = track_details.track_name
        if map_details:
            self.width = map_details.width
            self.height = map_details.height
            self.x_offset = map_details.x_offset
            self.y_offset = map_details.y_offset
            self.margin = map_details.margin
        self.image = map_image_data

    def as_state(self):
        has_track_details = bool(self.track_name)
        has_map_details = bool(
            self.width and self.height and self.x_offset and self.y_offset
        )
        map_margin_ok = bool(self.margin and math.floor(self.margin) == 10)
        has_map = bool(self.image)
        return TrackDataState(
            has_track_details=has_track_details,
            has_map_details=has_map_details,
            map_margin_ok=map_margin_ok,
            has_map=has_map,
        )


class RequestTrackPayload(BaseRequestPayload):
    _json_field_names = {"track_id": "trackId"}

    def __init__(self, track_id):
        # type: (str) -> None
        self.track_id = track_id


class RequestTrackResponse:
    _json_field_names = {"exists": "exists", "track_data": "trackData"}

    def __init__(self, json_data):
        # type: (dict) -> None
        self.exists = bool(json_data.get("exists"))
        self.track_data = TrackDataPayload.from_json_dict(
            json_data.get(self._json_field_names["track_data"]), {"image": "url"}
        )
