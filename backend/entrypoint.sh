#!/bin/sh
set -e

python manage.py migrate --noinput
python manage.py import_questions /app/namunalar/questions.json --if-empty
python manage.py ensure_superuser
python manage.py collectstatic --noinput >/dev/null

exec "$@"
