"""
Stage 2: idempotency support (stub).
TODO: detect Idempotency-Key header, check store (e.g. Redis/cache), return cached
response for duplicate POST/PATCH or allow request and cache response.
"""


class IdempotencyMiddleware:
    """
    Stub middleware for idempotent requests.
    When implemented: look for Idempotency-Key header on POST/PUT/PATCH,
    check cache/store; if key seen, return cached response; else allow request
    and cache response by key (with TTL).
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        return self.get_response(request)
