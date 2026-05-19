import queue
import threading
import traceback

from src.plogging import pLogger

log = pLogger(__name__).worker_log


class Worker:
    def __init__(self):
        self._queue = queue.Queue()
        self._thread = threading.Thread(name="pdata_worker", target=self._run)
        self._thread.daemon = False
        self._thread.start()
        log("Worker started")

    def enqueue(self, task):
        log("Queue Size: {}".format(self._queue.qsize()))
        log("Unfinished Tasks: {}".format(self._queue.unfinished_tasks))
        self._queue.put(task)

    def stop(self):
        log("Breaking Task Queue...")
        self._queue.put(None)
        log("Logging Thread State")
        for t in threading.enumerate():
            log(t.name, t.is_alive())
        log("Joining Thread...")
        self._thread.join()
        log("Thread Joined")

    def _run(self):
        while True:
            task = self._queue.get()
            if task is None:
                log("Task Queue Interrupted")
                break
            try:
                task()
            except:  # pylint: disable=W0702
                log(traceback.format_exc())
        log("Thread Stopped")


worker = Worker()
