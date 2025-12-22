#!/usr/bin/env bash
set -e

echo "Waiting for MySQL..."

python - <<EOF
import socket, time
host = "panchang_django_mysql"
port = 3306
while True:
    try:
        s = socket.create_connection((host, port), 2)
        s.close()
        break
    except Exception:
        print("Waiting for MySQL...")
        time.sleep(2)
EOF

python manage.py migrate
exec gunicorn panchang_api.wsgi:application --bind 0.0.0.0:8000
