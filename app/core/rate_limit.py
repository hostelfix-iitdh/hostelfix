from collections import defaultdict, deque
from threading import Lock
from time import monotonic

from fastapi import HTTPException, Request


class RateLimiter:
    def __init__(self):
        self._events = defaultdict(deque)
        self._lock = Lock()

    def check(
        self,
        key: str,
        limit: int,
        window_seconds: int,
        message: str = "Too many requests. Please try again later.",
    ) -> None:
        now = monotonic()
        with self._lock:
            q = self._events[key]
            cutoff = now - window_seconds
            while q and q[0] <= cutoff:
                q.popleft()
            if len(q) >= limit:
                raise HTTPException(429, message)
            q.append(now)


rate_limiter = RateLimiter()


def client_key(request: Request, suffix: str = "") -> str:
    host = request.client.host if request.client else "unknown"
    return f"{host}:{suffix}"
