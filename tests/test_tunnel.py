"""Tunnel module tests: status, URL extraction."""

from core.tunnel import get_tunnel_url, tunnel_status
from core.queue import queue, rate_limiter


class TestTunnelStatus:
    def test_tunnel_not_running_by_default(self):
        from core.tunnel import stop_tunnel
        stop_tunnel()
        status = tunnel_status()
        assert "running" in status
        assert "url" in status
        assert "pid" in status
        assert status["running"] is False

    def test_get_tunnel_url_default(self):
        from core.tunnel import stop_tunnel
        stop_tunnel()
        url = get_tunnel_url()
        assert url is None


class TestModuleImports:
    def test_queue_imports(self):
        assert queue is not None
        assert rate_limiter is not None

    def test_queue_attributes(self):
        assert hasattr(queue, "enqueue")
        assert hasattr(queue, "acquire_ollama")
        assert hasattr(queue, "release_ollama")
        assert hasattr(queue, "get_position")

    def test_rate_limiter_attributes(self):
        assert hasattr(rate_limiter, "check")
        assert rate_limiter.max_requests == 20
        assert rate_limiter.window == 60
