from datetime import datetime
import os
import json
import ac

SESSION_LUT = (
    (0, "PRACTICE"),
    (1, "QUALIFY"),
    (2, "RACE"),
)


class LapController:
    def __init__(self, session_id, instance_track, instance_car, *args, **kwargs):
        self.event_time = datetime.now().strftime("%d%m%Y%H%M")
        self.session_time = datetime.now().strftime("%d%m%Y_%H%M")
        self.track = instance_track
        self.session_id = session_id
        self.car = instance_car
        self.laps = []

        self.current_lap = 0
        self.lap_invalid = False
        self.pit_lap = False
        self.lap_data_points = []

    def get_export_data(self):
        data = {
            "eventTime": self.event_time,
            "sessionTime": self.session_time,
            "track": self.track,
            "car": self.car,
            "sessionType": self.get_session(),
            "lapCount": self.current_lap,
            "laps": self.laps,
        }
        return data

    def end_session(self):
        s = self.get_export_data()
        # TODO: Catch only discarded laps?
        if len(s["laps"]) == 0:
            return
        log_dir = os.path.join(os.path.expanduser("~"), "Documents")
        file_name = "{}-{}-{}-{}_laps-{}.json".format(
            self.track, self.car, self.get_session(), self.current_lap, self.session_time
        )
        b = json.dumps(s)
        with open(os.path.join(log_dir, file_name), "w") as f:
            f.writelines(b)

    def start_session(self, s_id: int):
        # Close the last session
        self.end_session()
        self.session_time = datetime.now().strftime("%d%m%Y_%H%M")
        self.session_id = s_id
        
        # Reset the lap data and tracker
        self.laps = []
        self.start_lap(0)

    def get_session(self):
        return SESSION_LUT[self.session_id][1]

    def end_event(self):
        self.end_session()
        pass

    def start_lap(self, lap_number):
        self.current_lap = lap_number
        self.lap_data_points = []
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
        ac.log(
            "Session {} Lap {}: {} | Pit: {} | Invalid: {}".format(
                self.session_id, self.current_lap, lap_time, self.pit_lap, self.lap_invalid
            )
        )
        if self.session_id == 2:
            # Race rules - keep all the laps
            self.laps.append(lap_data)
        elif self.session_id == 1:
            # Quali rules - keep invalid, discard pit
            if not self.pit_lap:
                self.laps.append(lap_data)
            else:
                ac.log('Discarding Quali Lap')
                self.laps.append(
                    {"lap_number": self.current_lap, "discard": True, "pit_lap": self.pit_lap}
                )
        else:  # self.session_id == 0
            # Practice Rules - only keep valid
            if not self.pit_lap and not self.lap_invalid:
                ac.log('Storing Practice Lap: {} {}'.format(self.pit_lap, self.lap_invalid))
                self.laps.append(lap_data)
            else:
                ac.log('Discarding Practice Lap')
                self.laps.append(
                    {
                        "lap_number": self.current_lap,
                        "discard": True,
                        "pit_lap": self.pit_lap,
                        "invalid": self.lap_invalid,
                    }
                )
        self.start_lap(self.current_lap + 1)

    def add_lap_data(self, data):
        self.lap_data_points.append(data)

    def invalidate_lap(self):
        # ac.log("Invalidated Lap {}".format(self.lap_count))
        self.lap_invalid = True

    def set_pit_lap(self):
        # ac.log("Pit Lap {}".format(self.lap_count))
        self.pit_lap = True
