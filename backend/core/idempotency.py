import hashlib

from django.conf import settings
from django.core.cache import cache
from django.http import HttpResponse, JsonResponse


class IdempotencyMiddleware:
    supported_methods = {"POST", "PUT", "PATCH", "DELETE"}

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if not self._should_handle(request):
            return self.get_response(request)

        cache_key = self._build_cache_key(request)
        lock_key = f"{cache_key}:lock"
        fingerprint = self._body_fingerprint(request)

        cached_response = cache.get(cache_key)
        if cached_response:
            return self._replay_or_reject(cached_response, fingerprint)

        if not cache.add(lock_key, fingerprint, timeout=settings.IDEMPOTENCY_LOCK_TTL):
            cached_response = cache.get(cache_key)
            if cached_response:
                return self._replay_or_reject(cached_response, fingerprint)

            return JsonResponse(
                {"detail": "A request with this Idempotency-Key is already being processed."},
                status=409,
            )

        try:
            response = self.get_response(request)
            if self._should_store(response):
                self._store_response(cache_key, fingerprint, response)
            return response
        finally:
            cache.delete(lock_key)

    def _should_handle(self, request):
        key = request.headers.get("Idempotency-Key")
        return (
            getattr(settings, "IDEMPOTENCY_ENABLED", True)
            and request.method in self.supported_methods
            and request.path.startswith("/api/")
            and bool(key)
        )

    def _build_cache_key(self, request):
        if getattr(request, "user", None) and request.user.is_authenticated:
            scope = f"user:{request.user.pk}"
        else:
            scope = f"anon:{request.META.get('REMOTE_ADDR', 'unknown')}"
        raw_key = "|".join([
            scope,
            request.method,
            request.get_full_path(),
            request.headers["Idempotency-Key"],
        ])
        digest = hashlib.sha256(raw_key.encode("utf-8")).hexdigest()
        return f"idempotency:{digest}"

    def _body_fingerprint(self, request):
        body = request.body or b""
        return hashlib.sha256(body).hexdigest()

    def _replay_or_reject(self, cached_response, fingerprint):
        if cached_response["fingerprint"] != fingerprint:
            return JsonResponse(
                {"detail": "This Idempotency-Key was already used with a different request body."},
                status=409,
            )

        response = HttpResponse(
            content=cached_response["content"],
            status=cached_response["status"],
            content_type=cached_response["content_type"],
        )
        for header, value in cached_response["headers"].items():
            response[header] = value
        response["X-Idempotent-Replay"] = "true"
        return response

    def _should_store(self, response):
        return getattr(response, "streaming", False) is False and response.status_code < 500

    def _store_response(self, cache_key, fingerprint, response):
        if hasattr(response, "render") and not getattr(response, "is_rendered", True):
            response.render()

        payload = {
            "fingerprint": fingerprint,
            "status": response.status_code,
            "content": bytes(response.content),
            "content_type": response.get("Content-Type", "application/octet-stream"),
            "headers": {
                header: value
                for header, value in response.items()
                if header.lower() not in {"content-type", "content-length"}
            },
        }
        cache.set(cache_key, payload, timeout=settings.IDEMPOTENCY_CACHE_TTL)
