# pData - Assetto Corsa Telemetry App

A Python app for Assetto Corsa that collects per-meter telemetry data (speed, throttle, brake, gear, steering, RPM, position) and uploads it to a cloud API for later analysis.

## Python Version Constraint

**Python 3.3.5 — fixed and immutable.** AC embeds its own Python runtime; this cannot be changed.

Implications:
- No f-strings (use `.format()`)
- No type annotations (avoid them entirely)
- No `yield from`, no `async`/`await`
- No `pathlib`, no `enum` (unless bundled)
- `print()` is available but **do not use it** — use `plogging.log()` instead

## Project Structure

```
pData.py              # App entry point — defines acMain, acUpdate, acShutdown
LapController.py      # Session and lap lifecycle management + data export
ext_requests.py       # HTTP upload helpers (threaded, using bundled requests)
plogging.py           # Logging wrapper around ac.log
data_displays/        # On-screen UI modules (each creates its own ac app window)
  invalid_lap.py      # InvalidLapDisplay — shows invalid/pit lap state
deps/                 # Bundled third-party libraries (not from pip at runtime)
  requests/           # HTTP library (bundled, used via ext_requests)
  stdlib64/           # Native C extensions required by AC's Python
    sim_info.py       # Shared memory wrapper (ctypes) — primary telemetry source
    _ctypes.pyd
    _socket.pyd
    _ssl.pyd
docs/                 # AC API documentation PDFs (reference these for AC API usage)
  ACPythonDocumentation.pdf
  ACSharedMemoryDocumentation.pdf
```

## AC App Lifecycle

Every AC Python app must implement these top-level functions:

```python
def acMain(ac_version):
    # Called once on load. Set up UI, initialise state.
    # Must return the app name string (e.g. "pData")
    return "pData"

def acUpdate(deltaT):
    # Called every frame. deltaT is time since last frame in seconds.
    pass

def acShutdown():
    # Called when AC exits or session ends. Flush/save data here.
    pass
```

## AC Python API

The `ac` module is built in to AC's runtime — never import it from deps.

Key functions used in this project:
- `ac.newApp(name)` — create a new app window; name must be unique across all AC apps
- `ac.getCarState(car_idx, acsys.CS.<field>)` — per-frame telemetry
- `ac.getTrackName(0)`, `ac.getTrackLength(0)`, `ac.getTrackConfiguration(0)`
- `ac.getDriverName(0)`, `ac.getCarName(0)`
- `ac.isCarInPitlane(car_idx)`
- `ac.log(text)` — writes to AC's log file (use `plogging.log()` as wrapper)
- `ac.console(text)` — writes to the in-game console (use sparingly, for debugging only)

The `acsys` module defines constants (e.g. `acsys.CS.SpeedKMH`, `acsys.CS.LapCount`).

## Shared Memory (`sim_info`)

`sim_info.py` (in `deps/stdlib64/`) wraps AC's shared memory via `ctypes` and `mmap`.

```python
from sim_info import info

info.graphics.status   # AC_OFF=0, AC_REPLAY=1, AC_LIVE=2, AC_PAUSE=3
info.graphics.session  # AC_PRACTICE=0, AC_QUALIFY=1, AC_RACE=2, AC_HOTLAP=3, ...
info.physics.numberOfTyresOut  # int: number of tyres currently off-track
```

**The app only activates when `info.graphics.status == 2` (AC_LIVE).** It returns early in `acMain` and skips updates otherwise.

## Threading

Threading works via Python's standard `threading` module. Background threads are used for HTTP uploads so they don't block the game loop. Thread naming convention: prefix with `pdata_` (e.g. `pdata_session_upload`, `pdata_track_check`) so `acShutdown` can identify and join them.

```python
# acShutdown waits for all pdata-prefixed threads
for thread in threading.enumerate():
    if thread.name.startswith("pdata"):
        thread.join()
```

## Data Model

Telemetry is stored as a list of per-meter data points:
- `lap_data_points` — list of length `track_length` (in metres), indexed by floor(track_distance)
- Each point: `{'lapTime', 'speed', 'gas', 'brake', 'gear', 'steer', 'rpm', 'pos'}`
- Points are collected once per metre (using `NormalizedSplinePosition * track_length`)
- Duplicate and early-in-metre readings are discarded to ensure one clean sample per metre

Session export shape:
```json
{
  "eventTime": "ISO8601",
  "driver": "...",
  "sessionTime": "ISO8601",
  "track": "track_name[_layout]",
  "car": "...",
  "sessionType": "PRACTICE|QUALIFY|RACE|HOTLAP",
  "lapCount": 5,
  "fastestLap": 3,
  "fastestLapTime": 92000,
  "laps": [ { "lap_number": 1, "lap_time": ..., "invalid": false, "pit_lap": false, "lap_data": [...] } ]
}
```

**Lap filtering rules:**
- Non-race sessions: discard invalid laps AND pit laps entirely
- Race sessions: keep pit laps, discard invalid laps (stored with `"discard": true`)

## Cloud API

Endpoints are hardcoded in `ext_requests.py` (Google Cloud Run). All sends are fire-and-forget threads. Two operations:
1. `send_session_data(json_str)` — uploads full session on end
2. `send_track_check(track_data_str, track_name)` — checks if track exists, uploads map/ini if not

## UI Conventions

- Keep app windows **small and unobtrusive**
- Each UI component creates its own `ac.newApp()` window with a unique name
- Hide the title bar icon: `ac.setIconPosition(app, -10000, -10000)` or `(-100, -100)`
- The main config window (`pData`) shows checkboxes; the `pData_LapState` window shows lap state
- App names registered with `ac.newApp()` must be globally unique across all AC Python apps

## Workflow Preferences

- **Never auto-commit.** Always ask before creating a git commit.
- **Use `plogging.log()`** (or `ac.log()` directly) for all logging. Never use `print()`.
- **No type annotations** — they are unnecessary and can cause issues in Python 3.3.
- Avoid adding docstrings or comments to code that wasn't changed.
- Prefer editing existing files over creating new ones.

## stdlib Availability

The following are bundled in `deps/stdlib64/` because they are not available in AC's default Python path:
- `sim_info.py` — shared memory (project-specific, not stdlib)
- `_ctypes.pyd`, `_socket.pyd`, `_ssl.pyd`, `unicodedata.pyd` — native extensions

Standard modules confirmed working: `threading`, `datetime`, `os`, `json`, `math`, `configparser`, `base64`, `mmap`, `ctypes`, `functools`.

Unknown availability: `subprocess`, `multiprocessing`, `urllib`, `http.client`, `socket` (direct use — `_socket.pyd` is bundled). When in doubt, check `deps/` before using a stdlib module, and test in-game.

## Reference Docs

- `docs/ACPythonDocumentation.pdf` — full AC Python API reference
- `docs/ACSharedMemoryDocumentation.pdf` — shared memory struct definitions
