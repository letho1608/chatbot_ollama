import os
import subprocess
import sys
import json
import urllib.request
import shutil
import urllib.error

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
REQUIRED_MODELS = ["minimax-m3:cloud", "nomic-embed-text:latest"]
OLLAMA_URL = "http://127.0.0.1:11434"


CHECK = "\u2713"
CROSS = "\u2717"
ARROW = "\u25b6"

def log(msg, status="INFO"):
    icons = {"OK": CHECK, "FAIL": CROSS, "INFO": ARROW}
    print(f"  [{icons.get(status, ARROW)}] {msg}")


def check_ollama():
    log("Checking if Ollama is running...")
    try:
        req = urllib.request.Request(f"{OLLAMA_URL}/api/tags")
        with urllib.request.urlopen(req, timeout=5) as resp:
            data = json.loads(resp.read())
            installed = [m["name"] for m in data.get("models", [])]
            log(f"Ollama OK. Installed models: {len(installed)}", "OK")
            return installed
    except Exception as e:
        log(f"Ollama not reachable at {OLLAMA_URL}: {e}", "FAIL")
        log("Make sure Ollama is installed and running (ollama serve)", "INFO")
        return None


def pull_model(model_name):
    log(f"Pulling model: {model_name}...")
    try:
        data = json.dumps({"name": model_name}).encode()
        req = urllib.request.Request(
            f"{OLLAMA_URL}/api/pull", data=data,
            headers={"Content-Type": "application/json"}
        )
        with urllib.request.urlopen(req, timeout=600) as resp:
            for line in resp.read().decode().strip().split("\n"):
                if line:
                    status = json.loads(line).get("status", "")
                    if status == "success":
                        log(f"Model {model_name} pulled", "OK")
                        return True
        log(f"Model {model_name} pull completed", "OK")
        return True
    except Exception as e:
        log(f"Failed to pull {model_name}: {e}", "FAIL")
        return False


def install_python_deps():
    log("Installing Python dependencies...")
    req_file = os.path.join(BASE_DIR, "requirements.txt")
    if not os.path.exists(req_file):
        log("requirements.txt not found", "FAIL")
        return False
    try:
        subprocess.run(
            [sys.executable, "-m", "pip", "install", "-r", req_file],
            check=True, capture_output=True
        )
        log("Python dependencies installed", "OK")
        return True
    except subprocess.CalledProcessError as e:
        log(f"pip install failed: {e.stderr.decode()[:200]}", "FAIL")
        return False


def check_cloudflared():
    log("Checking cloudflared...")
    cf = shutil.which("cloudflared")
    if cf:
        log(f"cloudflared found at {cf}", "OK")
        return True
    log("cloudflared not found. Install from: https://developers.cloudflare.com/cloudflare-one/connections/connect-networks/downloads/", "FAIL")
    log("Or use winget: winget install Cloudflare.Cloudflared", "INFO")
    return False


def create_data_dir():
    data_dir = os.path.join(BASE_DIR, "data")
    os.makedirs(data_dir, exist_ok=True)
    log(f"Data directory ready: {data_dir}", "OK")


def create_gitignore():
    gitignore = os.path.join(BASE_DIR, ".gitignore")
    if not os.path.exists(gitignore):
        with open(gitignore, "w") as f:
            f.write("__pycache__/\n*.pyc\n*.pyo\n.env\nvenv/\n.venv/\n*.db\nserver.log\ntoken.json\n")
        log(".gitignore created", "OK")


def main():
    print("=" * 50)
    print("  Tysor - Cyber Security AI Chatbot Setup")
    print("=" * 50)
    print()

    install_python_deps()

    print()
    models = check_ollama()
    if models is not None:
        for model in REQUIRED_MODELS:
            short = model.split(":")[0]
            if any(short in m for m in models):
                log(f"Model {model} already installed", "OK")
            else:
                pull_model(model)

    print()
    check_cloudflared()

    print()
    create_data_dir()
    create_gitignore()

    print()
    print("=" * 50)
    print("  Setup complete!")
    print()
    print("  Start the server:")
    print(f"    python -m uvicorn app_backend:app --host 127.0.0.1 --port 8000")
    print()
    print("  Open browser:")
    print("    http://127.0.0.1:8000")
    print()
    print("  Test accounts:")
    print("    User:  testuser / test123")
    print("    Admin: admin   / admin123")
    print("=" * 50)


if __name__ == "__main__":
    main()
