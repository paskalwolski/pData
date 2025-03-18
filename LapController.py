from datetime import datetime
import os
import json
import ac
import threading
import configparser
import base64

from plogging import log

from ext_requests import send_session_data, send_track_check 

SESSION_LUT = (
    (0, "PRACTICE"),
    (1, "QUALIFY"),
    (2, "RACE"),
)

class LapController:

    global track_exists

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
        self.fastest_lap = None
        self.fastest_lap_time = None
        self.laps = []
        self.driver = driver

        self.current_lap = 0
        self.lap_invalid = False
        self.pit_lap = False
        self.lap_data_points = [None for _ in range(track_length)]

        self.is_logging = False
        self.is_uploading = False

        # Track Detail upload
        self.check_track()
    
    @property
    def track_name(self):
        if self.track:
            return self.circuit + "_" + self.track
        else:
            return self.circuit

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
            assert params["margin"] == '10'
            
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
                'image': base64.b64encode(img).decode('utf-8'),
            }

            # # Debug Request
            # send_track_check(track_details)
            # Create the thread
            request_thread = threading.Thread(target=send_track_check, args=(track_details))
            request_thread.daemon = True
            request_thread.start()
        except AssertionError:
            log("Unexpected Margin Found - Not sending Track Update")
        except Exception as e:
            log("An Error occured locating track file: {}".format(e))

    def get_export_data(self):
        data = {
            "eventTime": self.event_time.isoformat(),
            "driver": self.driver,
            "sessionTime": self.session_time.isoformat(),
            "track": self.track_name,
            "car": self.car,
            "sessionType": self.get_session(),
            "lapCount": self.current_lap,
            "fastestLap": self.fastest_lap,
            "fastestLapTime": self.fastest_lap_time,
            "laps": self.laps,
        }
        return data

    def end_session(self, wait_flag=False):
        s = self.get_export_data()
        # TODO: Catch only discarded laps?
        if len(s["laps"]) == 0:
            return
        log_dir = os.path.join(os.path.expanduser("~"), "Documents")
        file_name = "{}-{}-{}-{}_laps-{}.json".format(
            self.track_name,
            self.car,
            self.get_session(),
            self.current_lap,
            self.session_time.strftime("%d%m%Y%H%M"),
        )
        b = json.dumps(s)
        if self.is_logging:
            with open(os.path.join(log_dir, file_name), "w") as f:
                f.writelines(b)
        if self.is_uploading:
            self.prep_session_send(s, wait_flag)
        if not self.is_logging and not self.is_uploading:
            log("Data not Logged")

    def prep_session_send(self, data: str, wait_flag: bool = False):
        if isinstance(data, dict):
            data = json.dumps(data)

        # # debug send
        # send_session_data(data)
        
        # Thread Send
        request_thread = threading.Thread(target=send_session_data, args=(data))
        request_thread.daemon = True
        request_thread.start()
        if wait_flag: request_thread.join()

    def start_session(self, s_id: int):
        # Close the last session
        self.end_session()
        self.session_time = datetime.now()
        self.session_id = s_id

        # Reset the lap data and tracker
        self.laps = []
        self.start_lap(0)

    def get_session(self):
        return SESSION_LUT[self.session_id][1]

    def end_event(self):
        self.end_session(wait_flag=True)
        pass

    def start_lap(self, lap_number, last_lap_time=None):
        if last_lap_time:
            self.end_lap(last_lap_time)
        self.current_lap = lap_number
        self.lap_data_points = [None for _ in range(self.track_length)]
        self.lap_invalid = False
        self.pit_lap = False
        # TODO: Add logic for catchign a start behind teh s/f line

    def end_lap(self, lap_time):
        lap_data = {
            "lap_number": self.current_lap,
            "lap_data": self.lap_data_points,
            "lap_time": lap_time,
            "invalid": self.lap_invalid,
            "pit_lap": self.pit_lap,
        }
        log(
            "Session {} Lap {}: {} | Pit: {} | Invalid: {}".format(
                self.session_id,
                self.current_lap,
                lap_time,
                self.pit_lap,
                self.lap_invalid,
            )
        )
        if self.session_id == 2:
            # Race - we want to keep pit laps and discard invalids
            if self.lap_invalid:
                self.laps.append(
                    {
                        "lap_number": self.current_lap,
                        "discard": True,
                        "invalid": self.lap_invalid,
                        "pit_lap": self.pit_lap,
                        "lap_time": lap_time,
                    }
                )
                return
        else:
            if self.lap_invalid or self.pit_lap:
                # Do nothing with useless laps
                return
        # Only valid laps here
        self.laps.append(lap_data)
        self.check_fastest_lap(lap_time)

    def set_fastest_lap(self, lap_number, lap_time):
        log("Setting fastest lap {}: {}".format(lap_number, lap_time))
        self.fastest_lap = lap_number
        self.fastest_lap_time = lap_time

    def check_fastest_lap(self, lap_time):
        if not self.fastest_lap:
            self.set_fastest_lap(self.current_lap, lap_time)
            return
        # Fastest lap already exists - check to see if this one was faster
        if lap_time < self.fastest_lap_time:
            self.set_fastest_lap(self.current_lap, lap_time)

    def add_lap_data(self, index, data):
        self.lap_data_points[index] = data

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