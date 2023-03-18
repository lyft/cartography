import time


class TimerError(Exception):
    """A custom exception used to report errors in use of Timer class"""


class Timer:
    def __init__(self):
        self._start_time = None

    def start(self):
        "Start the timer."
        if self._start_time is not None:
            raise TimerError("Timer is running. Use .stop() to stop it")
        self._start_time = time.perf_counter()

    def reset(self):
        "Reset the timer."
        self._start_time = None

    def check(self) -> float:
        "Check the # of seconds elapsed since the timer started"
        if self.is_started():
            return time.perf_counter() - self._start_time
        return 0.

    def is_started(self) -> bool:
        return self._start_time is not None
