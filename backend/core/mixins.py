"""
Stage 2: common mixins for views and serializers.
Extend as needed (e.g. OwnerQuerysetMixin, RequestUserMixin).
"""


class OwnerQuerysetMixin:
    """Mixin for ViewSets: filter queryset by request.user (owner field name configurable)."""

    owner_field = "user"

    def get_queryset(self):
        qs = super().get_queryset()
        if getattr(self, "swagger_fake_view", False):
            return qs.none()
        return qs.filter(**{self.owner_field: self.request.user})
