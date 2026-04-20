#!/bin/sh
set -eu

role="${1:-web}"

wait_for_postgres() {
  echo "Waiting for PostgreSQL..."
  python -c "import os, time, psycopg2
from psycopg2 import OperationalError

host = os.getenv('DB_HOST', 'db')
port = int(os.getenv('DB_PORT', '5432'))
name = os.getenv('DB_NAME', 'finance_accounting_db')
user = os.getenv('DB_USER', 'postgres')
password = os.getenv('DB_PASSWORD', '')

for attempt in range(60):
    try:
        conn = psycopg2.connect(
            host=host,
            port=port,
            dbname=name,
            user=user,
            password=password,
        )
    except OperationalError:
        time.sleep(2)
    else:
        conn.close()
        raise SystemExit(0)

raise SystemExit('PostgreSQL is unavailable after 120 seconds')
"
}

bootstrap_app() {
  python manage.py migrate --noinput
  python manage.py collectstatic --noinput
  python manage.py import_activities_code

  if [ "${LOAD_DEMO_DATA:-false}" = "true" ]; then
    python manage.py setup_demo_data --skip-if-populated
  fi

  python manage.py ensure_superuser
}

wait_for_postgres

case "$role" in
  web)
    bootstrap_app
    exec gunicorn config.wsgi:application \
      --bind 0.0.0.0:8000 \
      --workers "${GUNICORN_WORKERS:-3}" \
      --timeout "${GUNICORN_TIMEOUT:-120}"
    ;;
  worker)
    exec celery -A config worker -l "${CELERY_LOG_LEVEL:-info}"
    ;;
  beat)
    exec celery -A config beat -l "${CELERY_LOG_LEVEL:-info}" -s /tmp/celerybeat-schedule
    ;;
  *)
    shift || true
    exec "$role" "$@"
    ;;
esac
