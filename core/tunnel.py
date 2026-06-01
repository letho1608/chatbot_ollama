import asyncio
import subprocess
import threading
from typing import Optional


_tunnel_process: Optional[subprocess.Popen] = None
_tunnel_url: Optional[str] = None


def start_tunnel(port: int = 8000) -> str:
    global _tunnel_process, _tunnel_url
    if _tunnel_process and _tunnel_process.poll() is None:
        return _tunnel_url or "Tunnel is running"

    cmd = ["cloudflared", "tunnel", "--url", f"http://127.0.0.1:{port}"]
    _tunnel_process = subprocess.Popen(
        cmd,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        creationflags=subprocess.CREATE_NO_WINDOW,
    )

    def read_output():
        global _tunnel_url
        for line in iter(_tunnel_process.stdout.readline, ""):
            if "trycloudflare.com" in line:
                idx = line.index("https://")
                end = line.index(".trycloudflare.com") + len(".trycloudflare.com")
                _tunnel_url = line[idx:end]
                break

    t = threading.Thread(target=read_output, daemon=True)
    t.start()
    return "Starting tunnel..."


def stop_tunnel():
    global _tunnel_process, _tunnel_url
    if _tunnel_process:
        _tunnel_process.terminate()
        _tunnel_process = None
    _tunnel_url = None


def get_tunnel_url() -> Optional[str]:
    return _tunnel_url


def tunnel_status() -> dict:
    running = _tunnel_process is not None and _tunnel_process.poll() is None
    return {
        "running": running,
        "url": _tunnel_url or "",
        "pid": _tunnel_process.pid if running else 0,
    }
