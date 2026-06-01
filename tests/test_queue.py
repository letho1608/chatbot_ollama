"""Queue and rate limiter tests."""

import asyncio
import time
import pytest
from core.queue import queue, rate_limiter, AutoScalingQueue, RateLimiter


class TestRateLimiter:
    def test_allow_first_request(self):
        rl = RateLimiter(max_requests=5, window_seconds=60)
        ok, remaining = rl.check(1)
        assert ok is True
        assert remaining == 5

    def test_block_after_limit(self):
        rl = RateLimiter(max_requests=3, window_seconds=60)
        for _ in range(3):
            rl.check(2)
        ok, remaining = rl.check(2)
        assert ok is False

    def test_different_users_independent(self):
        rl = RateLimiter(max_requests=2, window_seconds=60)
        rl.check(3)
        rl.check(3)
        ok, _ = rl.check(4)
        assert ok is True

    def test_window_expiry(self):
        rl = RateLimiter(max_requests=2, window_seconds=1)
        rl.check(5)
        rl.check(5)
        ok1, _ = rl.check(5)
        assert ok1 is False
        time.sleep(1.1)
        ok2, _ = rl.check(5)
        assert ok2 is True


class TestAutoScalingQueue:
    @pytest.mark.asyncio
    async def test_enqueue_and_process(self):
        q = AutoScalingQueue(min_workers=1, max_workers=2)
        await q.start()
        results = []

        async def handler():
            results.append("done")

        item = await q.enqueue(1, "test", "conv-1", handler)
        assert item.user_id == 1
        assert item.username == "test"

        await asyncio.sleep(0.5)
        await q.stop()
        assert "done" in results

    @pytest.mark.asyncio
    async def test_position_tracking(self):
        q = AutoScalingQueue(min_workers=1, max_workers=2)
        await q.start()

        async def handler():
            await asyncio.sleep(0.3)

        await q.enqueue(1, "a", "conv-a", handler)
        await q.enqueue(1, "b", "conv-b", handler)

        await asyncio.sleep(0.1)
        pos_b = await q.get_position("conv-b")
        assert pos_b >= 1

        await q.stop()

    @pytest.mark.asyncio
    async def test_ollama_semaphore(self):
        sem_count = 0
        q = AutoScalingQueue(min_workers=1, max_workers=2)
        await q.start()
        sem_count = 0

        async def handler():
            nonlocal sem_count
            await q.acquire_ollama()
            sem_count += 1
            await asyncio.sleep(0.1)
            q.release_ollama()

        await q.enqueue(1, "a", "conv-1", handler)
        await q.enqueue(1, "b", "conv-2", handler)

        await asyncio.sleep(0.5)
        assert sem_count == 2
        await q.stop()

    @pytest.mark.asyncio
    async def test_scale_up_on_queue_depth(self):
        q = AutoScalingQueue(min_workers=1, max_workers=4, scale_up_qsize=2, scale_cooldown=0.5)
        await q.start()

        async def handler():
            await asyncio.sleep(0.2)

        # Enqueue many tasks to trigger scale-up
        for i in range(6):
            await q.enqueue(1, "test", f"conv-{i}", handler)

        await asyncio.sleep(1)
        assert q._worker_count >= 2
        await q.stop()


import pytest
