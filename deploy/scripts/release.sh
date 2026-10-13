#!/bin/sh
# One-off release step, run by the "migrate" service before "web" starts.
# Fails the deploy (non-zero exit) if any step fails.
set -eu

echo "[release] checking configuration"
python manage.py check --deploy --fail-level WARNING

echo "[release] applying migrations"
python manage.py migrate --noinput

echo "[release] collecting static files"
python manage.py collectstatic --noinput --clear

echo "[release] done"
