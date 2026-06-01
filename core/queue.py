import asyncio
import time
from collections import defaultdict
from dataclasses import dataclass, field
from typing import Optional


@dataclass
class QueueItem:
    user_id: int
    username: str
    conv_id: str
    position: int = 0


class RequestQueue:
    def __init__(self, max_concurrent: int = 1):
        self._semaphore = asyncio.Semaphore(max_concurrent)
        self._waiting: list[QueueItem] = []
        self._active: set[str] = set()
        self._lock = asyncio.Lock()

    async def enqueue(self, user_id: int, username: str, conv_id: str) -> QueueItem:
        async with self._lock:
            item = QueueItem(user_id, username, conv_id)
            if self._semaphore.locked():
                self._waiting.append(item)
                item.position = len(self._waiting)
            return item

    async def acquire(self) -> None:
        await self._semaphore.acquire()

    async def release(self, conv_id: str) -> None:
        async with self._lock:
            self._active.discard(conv_id)
        self._semaphore.release()
        async with self._lock:
            self._update_positions()

    def mark_active(self, conv_id: str) -> None:
        async def _mark():
            async with self._lock:
                self._active.add(conv_id)
                self._waiting[:] = [w for w in self._waiting if w.conv_id != conv_id]
                self._update_positions()
        asyncio.create_task(_mark())

    async def get_position(self, conv_id: str) -> int:
        async with self._lock:
            if conv_id in self._active:
                return 0
            for i, item in enumerate(self._waiting):
                if item.conv_id == conv_id:
                    return i + 1
            return 0

    def _update_positions(self):
        for i, item in enumerate(self._waiting):
            item.position = i + 1


queue = RequestQueue(max_concurrent=1)


class RateLimiter:
    def __init__(self, max_requests: int = 10, window_seconds: int = 60):
        self.max_requests = max_requests
        self.window = window_seconds
        self._buckets: dict[int, list[float]] = defaultdict(list)

    def check(self, user_id: int) -> tuple[bool, int]:
        now = time.time()
        cutoff = now - self.window
        bucket = self._buckets[user_id]
        bucket[:] = [t for t in bucket if t > cutoff]

        remaining = self.max_requests - len(bucket)
        if remaining <= 0:
            return False, 0

        bucket.append(now)
        return True, remaining


rate_limiter = RateLimiter(max_requests=20, window_seconds=60)
