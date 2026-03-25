from datetime import datetime
import os
import json
import ac
import configparser
import base64

from DataUploader import LapUploader, dispatch_track_check
from plogging import log

SESSION_LUT = (
    (0, "PRACTICE"),
    (1, "QUALIFY"),
    (2, "RACE"),
    (3, "HOTLAP"),
)

class TELEMETRY_POINTS:
    fields = ['lapTime','speed','gas','brake','gear','steer','rpm','pos','ers',]
    lapTime = 'lapTime'
    speed = 'speed'
    gas = 'gas'
    brake = 'brake'
    gear = 'gear'
    steer = 'steer'
    rpm = 'rpm'
    pos = 'pos'
    ers = 'ers'

class LapController:

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
        self.is_uploading = False
        self.is_uploading_track = False

        self.data_uploader = LapUploader(self.get_session_data())
        # Trigger an HTTP Session to the Functions
        self.data_uploader.dispatch_lap(None)

        # # Track Detail upload
        # self.check_track()

        # log("Currently {} thread open".format(threading.active_count()))
        # for thread in threading.enumerate():
        #     log("{}: {}".format(thread, thread.name))

        log("Completed Controller Setup")
    
    @property
    def track_name(self):
        if self.track:
            return self.circuit + "_" + self.track
        else:
            return self.circuit
        
    def _reset_data_points(self):
        self.lap_data_points = {f: [None for _ in range(self.track_length)] for f in TELEMETRY_POINTS.fields}

    def check_track(self):
        """
        Currently a 'check' that sends all the data even if it exists. Offloads the checking to the API
        Could be replaced with a GET that checks existing, and compares it to current - then updates if necessary
        """
        track_folder_path = os.path.join(os.getcwd(), "content", "tracks", self.circuit)
        if self.track:
            track_folder_path = os.path.join(track_folder_path, self.track)
        
        try:
            # Read the track ini data
            track_ini_path = os.path.join(track_folder_path, "data", "map.ini")
            cp = configparser.ConfigParser()
            cp.read(track_ini_path)
            params = cp['PARAMETERS']
            
            # Read the track image
            track_image_path = os.path.join(track_folder_path, "map.png")
            log("Using track file {}".format(track_image_path))
            with open(track_image_path, 'rb') as f:
                img = f.read()
            track_details = {
                # TODO: Check when the 20 margin is added...
                "trackName": self.track_name,
                "width": params["WIDTH"],
                "height": params["HEIGHT"],
                "xOffset": params["X_OFFSET"],
                "yOffset": params["Z_OFFSET"],
                "margin": params["MARGIN"],
                'image': base64.b64encode(img).decode('utf-8'),
            }

            dispatch_track_check(json.dumps(track_details), self.track_name)
        except Exception as e:
            log("Error with the track files")
            log(e)

   

    # TODO: Implement session logging
    # def log_session(self):
        # log_dir = os.path.join(os.path.expanduser("~"), "Documents")
        # file_name = "{}-{}-{}-{}_laps-{}.json".format(
        #     self.track_name,
        #     self.car,
        #     self.get_session(),
        #     self.current_lap,
        #     self.session_time.strftime("%d%m%Y%H%M"),
        # )
        # b = json.dumps(s)
        # if self.is_logging:
        #     with open(os.path.join(log_dir, file_name), "w") as f:
        #         f.writelines(b)

    def start_session(self, s_id):
        log("[session] start_session: {}".format(SESSION_LUT[s_id][1]))
        # Ensure we end a currently running session
        self.end_session()
        self.session_time = datetime.now()
        self.session_id = s_id

        self.data_uploader = LapUploader(self.get_session_data())

        # Reset the lap data and tracker
        self.laps = []

        self.start_lap(1)

    def end_session(self):
        log("[session] end_session: {} laps recorded".format(len(self.laps)))
        self.end_lap()
        if not self.laps:
            log("[session] end_session: no laps, skipping")
            return
        if self.is_logging:
            log('Session logging is not enabled')
            # self.log_session()

    def get_session(self):
        return SESSION_LUT[self.session_id][1]
    
    def get_session_data(self):
        return {
            "driver": self.driver,
            "car": self.car,
            "track": self.track_name,
            "sessionTime": self.session_time.isoformat(),
            "sessionType": self.get_session(),
            "eventTime": self.event_time.isoformat(),
        }
    
    def end_event(self):
        log("[event] end_event")
        self.end_session()

    def start_lap(self, lap_number, lap_time=None):
        log("[lap] start_lap: {} (lap_time={})".format(lap_number, lap_time))
        self.end_lap(lap_time)
        self.current_lap = lap_number
        # TODO: Add logic for catching a start behind the s/f line

    def end_lap(self, lap_time=None):
        log("[lap] end_lap: lap={} lap_time={}".format(self.current_lap, lap_time))
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
            
            log("[lap] end_lap: no lap_time, clearing state only")
            return

        log(
            "Session {} Lap {}: {} | Pit: {} | Invalid: {}".format(
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
        self.data_uploader.dispatch_lap(lap_data)
        ac.ext_perfEnd("pdata_lap_dispatch")

    def push_lap(self, lap_data):
        """Track a lap - either by overwriting an existing lap with the same data, or adding this as a new lap"""
        target_lap_number = lap_data['lapNumber']
        # Replace the latest lap if it tracks the same lap number - otherwise append
        if (self.laps[-1].get('lap_number') == target_lap_number):
            self.laps[-1] = lap_data
        else:
            self.laps.append(lap_data)
        # Send this lap to the backend - including lap number
        self.data_uploader.dispatch_lap(lap_data)

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

    def toggle_log(self, value):
        self.is_logging = value
        log("Logging: {}".format(self.is_logging))
    
    def toggle_upload(self, value):
        self.is_uploading = value
        log("Uploading: {}".format(self.is_uploading))

    def toggle_track_upload(self, value):
        self.is_uploading_track = value
        log("Uploading Track: {}".format(self.is_uploading_track))
        if self.is_uploading_track:
            self.check_track()