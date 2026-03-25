from django.conf import settings
from django.core.cache import cache
from django.db import transaction

from core.cache_utils import normalize_mapping, stable_digest


def get_finance_cache_version(user_id):
    key = f"finance:version:{user_id}"
    version = cache.get(key)
    if version is None:
        version = 1
        cache.set(key, version, timeout=None)
    return version


def build_finance_cache_key(namespace, user_id, payload=None):
    normalized_payload = normalize_mapping(payload or {})
    version = get_finance_cache_version(user_id)
    digest = stable_digest(normalized_payload)
    return f"finance:{namespace}:user:{user_id}:v:{version}:{digest}"


def invalidate_finance_cache(user_id):
    key = f"finance:version:{user_id}"
    version = cache.get(key)
    cache.set(key, (version or 1) + 1, timeout=None)


def invalidate_finance_cache_on_commit(user_id):
    transaction.on_commit(lambda: invalidate_finance_cache(user_id))


def get_cached_finance_payload(cache_key, builder, ttl=None):
    cached = cache.get(cache_key)
    if cached is not None:
        return cached

    payload = builder()
    cache.set(cache_key, payload, timeout=ttl or settings.FINANCE_CACHE_TTL)
    return payload
