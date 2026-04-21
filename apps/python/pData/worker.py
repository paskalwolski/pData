import queue
import threading
import traceback

from plogging import pLogger

log = pLogger(__name__).log


class Worker:
    def __init__(self):
        self._queue = queue.Queue()
        self._thread = threading.Thread(name="pdata_worker", target=self._run)
        self._thread.daemon = False
        self._thread.start()
        log("Worker started")

    def enqueue(self, task):
        self._queue.put(task)

    def stop(self):
        self._queue.put(None)
        self._thread.join()
        log("Worker stopped")

    def _run(self):
        while True:
            task = self._queue.get()
            if task is None:
                break
            try:
                task()
            except Exception:
                log("Worker error: {}".format(traceback.format_exc()))


worker = Worker()
