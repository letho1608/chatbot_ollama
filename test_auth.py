"""Test full auth flow: start server, login, call APIs with Bearer token."""
import json
import os
import subprocess
import sys
import time
import urllib.request
import urllib.error

os.chdir(os.path.dirname(os.path.abspath(__file__)))
DB_PATH = "data/chatbot.db"
if os.path.exists(DB_PATH):
    os.remove(DB_PATH)

proc = subprocess.Popen(
    [sys.executable, "-m", "uvicorn", "app_backend:app", "--host", "127.0.0.1", "--port", "8765"],
    stdout=subprocess.PIPE, stderr=subprocess.PIPE
)

time.sleep(4)

base = "http://127.0.0.1:8765"

try:
    # 1. Dashboard
    r = urllib.request.urlopen(f"{base}/", timeout=5)
    print(f"PASS Dashboard: {r.status} ({len(r.read())}b)")

    # 2. Register
    data = json.dumps({"username": "testuser", "email": "test@test.com", "password": "test123"}).encode()
    req = urllib.request.Request(f"{base}/api/auth/register", data=data, headers={"Content-Type": "application/json"})
    r = urllib.request.urlopen(req, timeout=5)
    result = json.loads(r.read())
    token = result["token"]
    print(f"PASS Register: {r.status}, token={token[:20]}...")

    # 3. Login
    data = json.dumps({"username": "admin", "password": "admin123"}).encode()
    req = urllib.request.Request(f"{base}/api/auth/login", data=data, headers={"Content-Type": "application/json"})
    r = urllib.request.urlopen(req, timeout=5)
    result = json.loads(r.read())
    admin_token = result["token"]
    print(f"PASS Login: {r.status}, token={admin_token[:20]}...")

    # 4. Direct DB check
    from database import init_db, get_db, User
    init_db()
    db = next(get_db())
    all_users = db.query(User).all()
    db.close()
    print(f"  DB users: {[(u.id, u.username, u.role, u.is_active) for u in all_users]}")

    # 5. /api/auth/me with Bearer token
    print(f"  Debug: token={admin_token[:30]}...")
    from auth import decode_token
    print(f"  Decoded: {decode_token(admin_token)}")
    req = urllib.request.Request(f"{base}/api/auth/me", headers={"Authorization": f"Bearer {admin_token}"})
    try:
        r = urllib.request.urlopen(req, timeout=5)
        me = json.loads(r.read())
        print(f"PASS /api/auth/me: {r.status}, user={me['username']}, role={me['role']}")
    except urllib.error.HTTPError as e:
        body = e.read().decode()
        print(f"FAIL /api/auth/me: {e.code}, body={body}")
        raise

    # 5. /api/conversations with Bearer token
    req = urllib.request.Request(f"{base}/api/conversations", headers={"Authorization": f"Bearer {admin_token}"})
    r = urllib.request.urlopen(req, timeout=5)
    print(f"PASS /api/conversations: {r.status}")

    # 6. Test chat page redirects without auth
    try:
        urllib.request.urlopen(f"{base}/chat", timeout=5)
        print("FAIL Should have gotten 401")
    except urllib.error.HTTPError as e:
        assert e.code == 401
        print(f"PASS Page without token: 401")

    # 7. /api/models
    req = urllib.request.Request(f"{base}/api/models", headers={"Authorization": f"Bearer {admin_token}"})
    r = urllib.request.urlopen(req, timeout=5)
    print(f"PASS /api/models: {r.status}")

    # 8. Admin: list users
    req = urllib.request.Request(f"{base}/api/admin/users", headers={"Authorization": f"Bearer {admin_token}"})
    r = urllib.request.urlopen(req, timeout=5)
    users = json.loads(r.read())
    print(f"PASS Admin users: {r.status}, count={len(users['users'])}")

    print("\n=== ALL TESTS PASSED ===")

except Exception as e:
    print(f"FAIL: {e}")
    import traceback
    traceback.print_exc()
finally:
    proc.kill()
    proc.wait()
    # Print server stderr for diagnostics
    _, err = proc.communicate()
    if err:
        print(f"\nServer stderr:\n{err.decode(errors='replace')[:2000]}")
