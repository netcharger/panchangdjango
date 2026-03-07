#!/usr/bin/env bash
set -e

echo "Faking initial panchang migration (tables already exist in DB)..."
python manage.py migrate panchang 0001 --fake --noinput

echo "Running remaining migrations..."
python manage.py migrate --noinput

echo "Starting Gunicorn..."
exec gunicorn panchang_api.wsgi:application --bind 0.0.0.0:8000
