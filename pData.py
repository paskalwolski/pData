import sys
import os
import traceback

_app_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(_app_dir, "deps", "stdlib64"))
sys.path.insert(0, os.path.join(_app_dir, "deps"))
os.environ["PATH"] = os.environ["PATH"] + ";."

# pylint: disable=C0413,C0411
import ac  # type: ignore
import acsys  # type: ignore
import threading
import math

from sim_info import info

from src.DataUploader import stop_worker
from src.plogging import pLogger
from src.controllers import EventController
from src.models import EventData, Telemetry, UpdatePayload, LapPayload
from src.services.AppConfig import app_config

# Load the config file as soon as we can
app_config.load(os.path.join(_app_dir, "pData.ini"))

# pylint: enable=C0413,C0411

SESSION_LUT = (
    (0, "PRACTICE"),
    (1, "QUALIFY"),
    (2, "RACE"),
    (3, "HOTLAP"),
)


log = pLogger(__name__).log

track_length = None  # type: int | None
last_meter = None  # type: int | None
event_controller = None  # type: EventController | None

# Best (smallest) delta-from-midpoint seen for the current meter
best_meter_delta = None  # type: int | None


def acMain(ac_version):  # pylint: disable=W0613
    global event_controller
    # Only enable the app for Live AC Mode
    if info.graphics.status != 2:
        log("AC is not Live. App disabled.")
        return "pData"

    event_controller = EventController(_get_event_data())

    return "pData"


def acUpdate(deltaT):  # pylint: disable=W0613
    global event_controller
    global last_meter, best_meter_delta
    try:

        # Skip update if app wasn't initialized (e.g., in replay mode)
        if not info.graphics.status == 2:
            return
        if event_controller is None:
            event_controller = EventController(_get_event_data())

        track_distance = round(
            ac.getCarState(0, acsys.CS.NormalizedSplinePosition)
            * event_controller.track_length,
            2,
        )
        track_meter = math.floor(track_distance)
        meter_delta = abs(
            (track_distance - track_meter) - 0.5
        )  # absolute distance from midpoint

        is_new_meter = track_meter != last_meter

        if not is_new_meter:
            # Same meter — skip if this reading is not closer to the midpoint
            if best_meter_delta is not None and meter_delta >= best_meter_delta:
                # Ignore this meter point - we already have a better one
                return

        else:
            # Track the meter and meter_delta
            last_meter = track_meter
            best_meter_delta = meter_delta

        # Track the meter based on spline distance - starting at meter 0
        spline_meter = track_meter - 1

        # Read telemetry when we are sure we'll use it
        update_payload = _get_update_payload(spline_meter)
        # Trigger the Controller Updates
        event_controller.update(update_payload)
    except Exception:
        log("ERROR", traceback.format_exc())


def acShutdown():
    global event_controller
    if not event_controller:
        log("Event Controller not initialised")
        return

    event_controller.close()
    stop_worker()
    log("[ac] Waiting for {} open threads...".format(threading.active_count()))
    for thread in threading.enumerate():
        if thread.name.startswith("pdata"):
            log("[ac] Waiting for thread {}".format(thread.name))
            thread.join(10)


def _get_update_payload(distance):
    # type: (int) -> UpdatePayload
    session_label = SESSION_LUT[info.graphics.session][1]
    lap_number = info.graphics.completedLaps + 1
    last_lap_time = info.graphics.lastTime

    lap_time = ac.getCarState(0, acsys.CS.LapTime)
    speed = round(ac.getCarState(0, acsys.CS.SpeedKMH), 2)
    gas = round(ac.getCarState(0, acsys.CS.Gas), 2)
    brake = round(ac.getCarState(0, acsys.CS.Brake), 2)
    gear = ac.getCarState(0, acsys.CS.Gear)
    steer = round(ac.getCarState(0, acsys.CS.Steer), 2)
    rpm = round(ac.getCarState(0, acsys.CS.RPM), 2)
    raw_pos = ac.getCarState(0, acsys.CS.WorldPosition)
    pos = [round(raw_pos[0], 1), round(raw_pos[1], 1), round(raw_pos[2], 1)]
    ers = round(info.physics.kersCurrentKJ, 2)

    invalid = True if info.physics.numberOfTyresOut > 3 else False
    pit = ac.isCarInPitlane(0)

    meter_telemetry = Telemetry(
        d=distance,
        lap_time=lap_time,
        speed=speed,
        gas=gas,
        brake=brake,
        gear=gear,
        steer=steer,
        rpm=rpm,
        pos_x=pos[0],
        pos_z=pos[2],
        ers=ers,
    )
    lap_data_payload = LapPayload(
        lap_number=lap_number,
        telemetry=meter_telemetry,
        invalid=invalid,
        in_pit=pit,
        last_lap_time=last_lap_time,
    )

    return UpdatePayload(session=session_label, lap_data=lap_data_payload)


def _get_event_data():
    return EventData(
        getattr(app_config, "username", ac.getDriverName(0)),
        # TODO: Improve fetching the track name
        ac.getTrackName(0),
        ac.getCarName(0),
        int(math.ceil(ac.getTrackLength())),
    )
