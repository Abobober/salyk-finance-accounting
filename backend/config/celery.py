import os

try:
    from celery import Celery
except ImportError:  # pragma: no cover
    celery_app = None
else:  # pragma: no cover
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')

    celery_app = Celery('config')
    celery_app.config_from_object('django.conf:settings', namespace='CELERY')
    celery_app.autodiscover_tasks()
    app = celery_app
