#!/usr/bin/env bash
set -e

echo "Waiting for MySQL..."

python - <<EOF
import socket, time, os

host = os.environ.get("MYSQL_HOST")
port = int(os.environ.get("MYSQL_PORT", 3306))

print(f"Using MySQL host: {host}:{port}")

while True:
    try:
        s = socket.create_connection((host, port), 2)
        s.close()
        break
    except Exception as e:
        print("Waiting for MySQL...", e)
        time.sleep(2)
EOF

echo "MySQL is ready. Running migrations..."
python manage.py migrate

echo "Starting Gunicorn..."
exec gunicorn panchang_api.wsgi:application --bind 0.0.0.0:8000
