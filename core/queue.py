import asyncio
import time
import logging
from collections import defaultdict
from dataclasses import dataclass, field
from typing import Optional, Callable, Awaitable


@dataclass
class QueueItem:
    user_id: int
    username: str
    conv_id: str
    handler: Optional[Callable[[], Awaitable[None]]] = None
    position: int = 0


class AutoScalingQueue:
    def __init__(self, min_workers: int = 2, max_workers: int = 6,
                 scale_up_qsize: int = 3, scale_down_qsize: int = 0,
                 scale_cooldown: float = 10.0):
        self._ollama_sem = asyncio.Semaphore(1)
        self._task_queue: asyncio.Queue[QueueItem] = asyncio.Queue()
        self._waiting: list[QueueItem] = []
        self._active: set[str] = set()
        self._lock = asyncio.Lock()

        self.min_workers = min_workers
        self.max_workers = max_workers
        self.scale_up_qsize = scale_up_qsize
        self.scale_down_qsize = scale_down_qsize
        self.scale_cooldown = scale_cooldown

        self._worker_count = min_workers
        self._last_scale_time = 0.0
        self._workers: set[asyncio.Task] = set()
        self._running = False

    async def start(self):
        self._running = True
        for i in range(self.min_workers):
            w = asyncio.create_task(self._worker_loop(i))
            self._workers.add(w)

    async def stop(self):
        self._running = False
        for w in self._workers:
            w.cancel()

    async def _worker_loop(self, wid: int):
        while self._running:
            try:
                item = await asyncio.wait_for(self._task_queue.get(), timeout=2)
            except asyncio.TimeoutError:
                await self._maybe_scale_down()
                continue

            try:
                async with self._lock:
                    self._active.add(item.conv_id)
                if item.handler:
                    await item.handler()
            except asyncio.CancelledError:
                raise
            except Exception as e:
                logging.exception(f"[Queue Worker {wid}] error: {e}")
            finally:
                async with self._lock:
                    self._active.discard(item.conv_id)
                    self._waiting[:] = [w for w in self._waiting if w.conv_id != item.conv_id]
                    self._update_positions()
                self._task_queue.task_done()
                await self._maybe_scale_up()

    async def enqueue(self, user_id: int, username: str, conv_id: str,
                      handler: Optional[Callable[[], Awaitable[None]]] = None) -> QueueItem:
        async with self._lock:
            item = QueueItem(user_id, username, conv_id, handler)
            self._waiting.append(item)
            item.position = len(self._waiting)
            await self._task_queue.put(item)
        await self._maybe_scale_up()
        return item

    async def acquire_ollama(self):
        await self._ollama_sem.acquire()

    def release_ollama(self):
        self._ollama_sem.release()

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

    async def _maybe_scale_up(self):
        async with self._lock:
            now = time.time()
            if now - self._last_scale_time < self.scale_cooldown:
                return
            qsize = self._task_queue.qsize()
            if qsize >= self.scale_up_qsize * self._worker_count and self._worker_count < self.max_workers:
                self._worker_count += 1
                self._last_scale_time = now
                w = asyncio.create_task(self._worker_loop(self._worker_count))
                self._workers.add(w)

    async def _maybe_scale_down(self):
        async with self._lock:
            now = time.time()
            if now - self._last_scale_time < self.scale_cooldown:
                return
            qsize = self._task_queue.qsize()
            if qsize <= self.scale_down_qsize and self._worker_count > self.min_workers:
                self._worker_count -= 1
                self._last_scale_time = now


queue = AutoScalingQueue(min_workers=2, max_workers=6)


class RateLimiter:
    def __init__(self, max_requests: int = 20, window_seconds: int = 60):
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
