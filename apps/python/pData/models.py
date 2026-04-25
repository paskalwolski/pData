from datetime import datetime
import json

# pylint: disable=line-too-long,R0902,R0913
# pylint: disable=R0913


class BaseRequestModel:
    """
    ABC that is used for data structures in outgoing requests which
    provides serialisation logic for camelCase network structures
    """

    _json_field_names = {}

    def to_dict(self):
        d = {}
        for f, j in self._json_field_names.items():
            v = getattr(self, f)
            d[j] = v.to_dict() if isinstance(v, BaseRequestModel) else v
        return d

    def to_json(self):
        return json.dumps(self.to_dict())


# Telemetry: Static bundle containing the telemtry data for a single meter
class Telemetry:
    _json_field_names = {
        "speed": "speed",
        "gas": "gas",
        "brake": "brake",
        "gear": "gear",
        "steer": "steer",
        "rpm": "rpm",
        "pos_x": "posX",
        "pos_z": "posZ",
        "ers": "ers",
    }

    def __init__(self, *, d, speed, gas, brake, gear, steer, rpm, pos_x, pos_z, ers):
        # type: (Telemetry, int, float, float, float, int, float, float, float, float, float) -> None
        self.d = d
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


class SessionData(BaseRequestModel):
    _json_field_names = {"event_data"}

    def __init__(self, event_data, session, session_timestamp, remote_session_id):
        # type: (EventData, str, datetime, str | None) -> None
        self.event_data = event_data
        self.session = session
        self.session_timestamp = session_timestamp
        self.remote_session_id = remote_session_id


class LapPayload:
    def __init__(self, *, lap_number, telemetry, invalid, in_pit, last_lap_time=None):
        # type: (LapPayload, int, Telemetry, bool, bool, float | None) -> None
        self.lap_number = lap_number
        self.telemetry = telemetry

        self.invalid = invalid
        self.in_pit = in_pit
        self.last_lap_time = last_lap_time


class UpdatePayload:
    def __init__(self, session, lap_data):
        # type: (UpdatePayload, str, LapPayload) -> None
        self.session = session
        self.lap_data = lap_data


class EventData:
    def __init__(self, driver, track, car, track_length):
        # type: (str, str, str, int) -> None
        self.driver = driver
        self.track = track
        self.track_length = track_length
        self.car = car


class SessionDataRequest(BaseRequestModel):
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
        self.driver = sessionData.event_data.driver
        self.track = sessionData.event_data.track
        self.session_time = sessionData.session_timestamp
        self.session_type = sessionData.session


class LapDataRequest(BaseRequestModel):
    _json_field_names = {
        "lap_number": "lapNumber",
        "lap_time": "lapTime",
        "is_valid": "isValid",
        "is_pit": "isPit",
        "discard": "discard",
        "lap_data": "lapData",
        "session_data": "sessionData",
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
        self.session_data = SessionDataRequest(session_data)
