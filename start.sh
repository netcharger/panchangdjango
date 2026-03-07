#!/usr/bin/env bash
set -e

echo "Running migrations..."
python manage.py migrate --fake-initial --noinput

echo "Starting Gunicorn..."
exec gunicorn panchang_api.wsgi:application --bind 0.0.0.0:8000
