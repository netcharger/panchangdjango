#!/usr/bin/env bash
set -e

echo "Waiting for MySQL..."

python - <<'EOF'
import os, time, socket
from urllib.parse import urlparse

u = urlparse(os.environ["DATABASE_URL"])
host = u.hostname
port = u.port or 3306

print(f"Using MySQL at {host}:{port}")

while True:
    try:
        s = socket.create_connection((host, port), 2)
        s.close()
        break
    except Exception as e:
        print("Waiting for MySQL...", e)
        time.sleep(2)
EOF

python manage.py migrate
exec gunicorn panchang_api.wsgi:application --bind 0.0.0.0:8000
