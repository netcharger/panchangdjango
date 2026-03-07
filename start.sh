#!/usr/bin/env bash
set -e

echo "Recording initial panchang migration as already applied..."
python manage.py shell -c "
from django.db.migrations.recorder import MigrationRecorder
from django.db import connection
recorder = MigrationRecorder(connection)
recorder.ensure_schema()
applied = {(m.app, m.name) for m in recorder.migration_qs}
if ('panchang', '0001_initial') not in applied:
    recorder.record_applied('panchang', '0001_initial')
    print('SUCCESS: Recorded panchang 0001_initial as applied')
else:
    print('SKIP: panchang 0001_initial already recorded')
"

echo "Running all remaining migrations..."
python manage.py migrate --noinput

echo "Starting Gunicorn..."
exec gunicorn panchang_api.wsgi:application --bind 0.0.0.0:8000
