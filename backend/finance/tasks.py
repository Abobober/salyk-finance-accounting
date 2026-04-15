from django.contrib.auth import get_user_model

from celery import shared_task
from finance.services.dashboard_service import get_dashboard_data


User = get_user_model()


@shared_task
def warm_dashboard_cache(user_id, filters=None):
    user = User.objects.filter(pk=user_id).first()
    if not user:
        return None
    return get_dashboard_data(user, filters=filters or {})
