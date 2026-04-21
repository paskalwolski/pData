# Worker Thread

A single module-level worker thread (`worker.py`) handles all background work across the controller hierarchy.

## How it works

The worker owns a `queue.Queue` and a single daemon thread. It accepts any callable and executes it sequentially:

```
worker.submit(fn)  →  queue  →  thread calls fn()
```

The worker has no knowledge of what it runs — it just calls whatever it receives.

## Controller responsibilities

Each controller owns its work logic in private methods. When a controller needs to offload work, it submits a lambda pointing to that method:

**Example — LapController:**
```python
def close(self, last_lap_time):
    worker.submit(lambda: self._process(last_lap_time))

def _process(self, last_lap_time):
    payload = self._prepare_telemetry_data()
    self._send(payload)
    # cleanup / register response
```

**Example — SessionController:**
```python
def close(self):
    worker.submit(lambda: self._close_session())

def _close_session(self):
    # finalise and send session data
```

Both controllers submit to the same queue, so work is processed in submission order.

## Shutdown

`acShutdown` imports the worker module directly and calls `worker.stop()`, which sends a sentinel and joins the thread. Because all work is sequential on a single thread, the queue is guaranteed to be drained before the thread exits.

```python
# pData.py
import worker

def acShutdown():
    event_controller.close()  # submits any final work
    worker.stop()             # waits for all submitted work to complete
```
