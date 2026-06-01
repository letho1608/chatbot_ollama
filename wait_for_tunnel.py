import sys
import os
import time

sys.path.insert(0, os.getcwd())
from core.tunnel import start_tunnel, get_tunnel_url

print('Starting tunnel...')
print()
start_tunnel(8000)

for _ in range(30):
    url = get_tunnel_url()
    if url:
        print('  === TUNNEL LIVE ===')
        print()
        print('  ' + url)
        print()
        break
    time.sleep(1)
else:
    print('  Tunnel URL not detected within 30s')
