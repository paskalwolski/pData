from datetime import datetime
import os
import json
import ac
import configparser
import base64

from DataUploader import LapUploader
from TrackDataController import TrackDataController
from plogging import log

SESSION_LUT = (
    (0, "PRACTICE"),
    (1, "QUALIFY"),
    (2, "RACE"),
    (3, "HOTLAP"),
)

class TELEMETRY_POINTS:
    fields = ['lapTime','speed','gas','brake','gear','steer','rpm','posX', 'posY', 'posZ','ers',]
    lapTime = 'lapTime'
    speed = 'speed'
    gas = 'gas'
    brake = 'brake'
    gear = 'gear'
    steer = 'steer'
    rpm = 'rpm'
    posX = 'posX'
    posY = 'posY'
    posZ = 'posZ'
    ers = 'ers'

class SessionController:

    def __init__(
        self,
        session_id,
        circuit_name,
        track_name,
        track_length,
        instance_car,
        driver,
        *args,
        **kwargs
    ):
        self.event_time = datetime.now()
        self.session_time = datetime.now()
        self.circuit = circuit_name
        self.track = track_name
        self.track_length = track_length
        self.session_id = session_id
        self.car = instance_car
        self.laps = []
        self.driver = driver

        self.current_lap = 1
        self.lap_invalid = False
        self.pit_lap = False
        self.lap_data_points = {}
        self._reset_data_points()

        self.is_logging = False
        self.is_uploading = True
        self.is_uploading_track = False
        log('controller initing')
        self.track_data_controller = TrackDataController(circuit_name, track_name)

        self.lap_uploader = LapUploader(self.get_session_data())
        # Trigger an HTTP Session to the Functions
        self.lap_uploader.dispatch_lap(None)


        # # Track Detail upload
        # self.check_track()

        # log("Currently {} thread open".format(threading.active_count()))
        # for thread in threading.enumerate():
        #     log("{}: {}".format(thread, thread.name))

        log("[controller] Completed Controller Setup")
    
        
    def _reset_data_points(self):
        self.lap_data_points = {f: [None for _ in range(self.track_length)] for f in TELEMETRY_POINTS.fields}

    def start_session(self, s_id):
        log("[controller] start_session: {}".format(SESSION_LUT[s_id][1]))
        # Ensure we end a currently running session
        self.end_session()
        self.session_time = datetime.now()
        self.session_id = s_id

        self.lap_uploader = LapUploader(self.get_session_data())

        # Reset the lap data and tracker
        self.laps = []

        self.start_lap(1)

    def end_session(self):
        lap_count = len(self.laps)
        log("[controller] end_session: {} laps recorded".format(lap_count))
        self.end_lap()
        if not self.laps:
            log("[controller] end_session: no laps, skipping")
            return
        self.lap_uploader.reset(lap_count)
        
        if self.is_logging:
            log('[controller] end_session: Session logging is not enabled')
            # self.log_session()

    def get_session(self):
        return SESSION_LUT[self.session_id][1]
    
    def get_session_data(self):
        return {
            "driver": self.driver,
            "car": self.car,
            "track": self.track_data_controller.track_id,
            "sessionTime": self.session_time.isoformat(),
            "sessionType": self.get_session(),
            "eventTime": self.event_time.isoformat(),
        }
    
    def end_event(self):
        log("[controller] end_event")
        self.end_session()

    def start_lap(self, lap_number, lap_time=None):
        log("[controller] start_lap: {} (lap_time={})".format(lap_number, lap_time))
        self.end_lap(lap_time)
        self.current_lap = lap_number
        # TODO: Add logic for catching a start behind the s/f line

    def end_lap(self, lap_time=None):
        log("[controller] end_lap: lap={} lap_time={}".format(self.current_lap, lap_time))
        # Always clear lap state, whether or not we upload
        lap_data_points = self.lap_data_points
        lap_invalid = self.lap_invalid
        pit_lap = self.pit_lap
        ac.ext_perfBegin("pdata_list_alloc")
        self._reset_data_points()
        ac.ext_perfEnd("pdata_list_alloc")
        self.lap_invalid = False
        self.pit_lap = False

        if not lap_time:
            
            log("[controller] end_lap: no lap_time, clearing Uploader state only")
            # TODO: Compare this with end_session, which also resets the uploader
            self.lap_uploader.reset(len(self.laps))
            return

        log(
            "[controller] Session {} Lap {}: {} | Pit: {} | Invalid: {}".format(
                self.session_id,
                self.current_lap,
                lap_time,
                pit_lap,
                lap_invalid,
            )
        )
        if self.session_id == 2:
            # Race - keep pit laps, discard invalids
            if lap_invalid:
                self.laps.append({
                    "lapNumber": self.current_lap,
                    "discard": True,
                    "isValid": not lap_invalid,
                    "isPit": pit_lap,
                    "lapTime": lap_time,
                })
                return
        else:
            if lap_invalid or pit_lap:
                return
        # Only valid laps here
        lap_data = {
            "lapNumber": self.current_lap,
            "lapTime": lap_time,
            "isValid": not lap_invalid,
            "isPit": pit_lap,
            "lapData": lap_data_points,
        }
        self.laps.append(lap_data)
        ac.ext_perfBegin("pdata_lap_dispatch")
        self.lap_uploader.dispatch_lap(lap_data)
        ac.ext_perfEnd("pdata_lap_dispatch")

    def add_lap_data(self, index, data):
        for k, v in data.items():
            if k in self.lap_data_points:
                self.lap_data_points[k][index] = v

    def invalidate_lap(self):
        # log("Invalidated Lap {}".format(self.lap_count))
        self.lap_invalid = True

    def set_pit_lap(self):
        # log("Pit Lap {}".format(self.lap_count))
        self.pit_lap = True
    
    def toggle_upload(self, value):
        self.is_uploading = value
        log("[controller] Uploading: {}".format(self.is_uploading))

    def toggle_track_upload(self, value):
        self.is_uploading_track = value
        log("[controller] Uploading Track: {}".format(self.is_uploading_track))
        if self.is_uploading_track:
            self.check_track()