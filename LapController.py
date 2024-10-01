from datetime import datetime

class LapController:
    def __init__(self, session_type, instance_track, instance_car, *args, **kwargs):
        self.time = datetime.now()
        self.track = instance_track
        self.session_type = session_type
        self.car = instance_car
        self.laps = []
        self.lap_count = 0
        self.lap_valid = True 
        self.pit_lap = False
        self.lap_data_points = []

    def start_session(self, type: str):
        self.set_session_type = type
        self.lap_count = 0
    
    def end_session(self):
        pass

    def end_lap(self, lap_time):
        self.laps.append({
            'lap_data': self.lap_data_points,
            'lap_time': lap_time,
            'valid': self.lap_valid,
            'pit_lap': self.pit_lap,
            })
        self.lap_count += 1
        self.lap_data_points = []
        self.lap_valid = True
        self.pit_lap = False

    def add_lap_data(self, data):
        self.lap_data_points.append(data)

    def invalidate_lap(self):
        self.lap_valid = False

    def set_pit_lap(self):
        self.pit_lap = True

    

