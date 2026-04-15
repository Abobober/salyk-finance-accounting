try:  # pragma: no cover
    from .celery import celery_app
except ImportError:  # pragma: no cover
    celery_app = None
