from datetime import datetime

# pylint: disable=line-too-long,R0902,R0913
# pylint: disable=R0913


# Telemetry: Static bundle containing the telemtry data for a single meter
class Telemetry:
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


class SessionData:
    def __init__(self, event_data, session, session_timestamp):
        # type: (EventData, str, datetime) -> None
        self.driver = event_data.driver
        self.track = event_data.track
        self.car = event_data.car
        self.session = session
        self.session_timestamp = session_timestamp


class LapData:
    def __init__(self, *, lap_number, telemetry, last_lap_time=None):
        # type: (LapData, int, Telemetry, float | None) -> None
        self.lap_number = lap_number
        self.telemetry = telemetry
        self.last_lap_time = last_lap_time


class UpdatePayload:
    def __init__(self, session, lap_data):
        # type: (UpdatePayload, str, LapData) -> None
        self.session = session
        self.lap_data = lap_data


class EventData:
    def __init__(self, driver, track, car):
        # type: (str, str, str) -> None
        self.driver = driver
        self.track = track
        self.car = car
