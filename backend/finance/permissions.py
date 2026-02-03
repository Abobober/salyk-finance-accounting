from rest_framework.permissions import BasePermission, SAFE_METHODS


class IsCategoryOwnerOrSystemReadOnly(BasePermission):
    """
    - System categories: read-only
    - User categories: only owner can modify
    """

    def has_object_permission(self, request, view, obj):
        if obj.is_system:
            return request.method in SAFE_METHODS
        return obj.user == request.user
