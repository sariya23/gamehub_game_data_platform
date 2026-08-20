import threading
import time
from dataclasses import dataclass


@dataclass(frozen=True)
class RateLimitConfig:
    requests: int
    period_seconds: float

    @property
    def interval(self) -> float:
        return self.period_seconds / self.requests


class RateLimiter:
    def __init__(self, config: RateLimitConfig):
        self._interval = config.interval
        self._last_request_at = 0.0
        self._lock = threading.Lock()

    def __enter__(self):
        with self._lock:
            now = time.monotonic()
            wait_for = self._interval - (now - self._last_request_at)

            if wait_for > 0:
                time.sleep(wait_for)

            self._last_request_at = time.monotonic()

        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        pass