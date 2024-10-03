from datetime import datetime
import os
import json
import ac

session_LUT = (
    (0, "PRACTICE"),
    (1, "QUALIFY"),
    (2, "RACE"),
)

class LapController:
    def __init__(self, session_id, instance_track, instance_car, *args, **kwargs):
        self.time = datetime.now()
        self.track = instance_track
        self.session_id = session_id
        self.car = instance_car
        self.laps = []
        self.lap_count = 0

        self.lap_valid = True 
        self.pit_lap = False
        self.lap_data_points = []

    def export_session(self):
        data = {
            'time': self.time.strftime("%d-%m-%y"),
            'track': self.track, 
            'car': self.car,
            'sessionType': self.get_session(),
            'lapCount': self.lap_count,
            'lap_data': self.laps,
        }
        return data

    def end_session(self):
        s = self.export_session()
        if len(s['lap_data']) == 0:
            return
        log_dir = os.path.join(os.path.expanduser("~"), "Documents")
        file_name = "{}-{}-{}-{}laps.json".format(self.track, self.car, self.get_session(), self.lap_count)
        b = json.dumps(s)
        with open(os.path.join(log_dir, file_name), "w") as f:
            f.writelines(b)    

    def start_session(self, type: int):
        self.end_session()
        self.session_id = type
        self.lap_count = 0

    def get_session(self):
        return session_LUT[self.session_id][1]
    
    def end_event(self):
        self.end_session()
        pass

    def start_lap(self):
        self.lap_count += 1
        self.lap_data_points = []
        self.lap_valid = True
        self.pit_lap = False
    
    def end_lap(self, lap_time):
        lap_data = {
            'lap_data': self.lap_data_points,
            'lap_time': lap_time,
            'valid': self.lap_valid,
            'pit_lap': self.pit_lap,
            }
        self.laps.append(lap_data)
        self.start_lap()
       

    def add_lap_data(self, data):
        self.lap_data_points.append(data)

    def invalidate_lap(self):
        self.lap_valid = False

    def set_pit_lap(self):
        self.pit_lap = True

    

