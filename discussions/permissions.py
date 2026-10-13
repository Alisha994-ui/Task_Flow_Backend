from rest_framework.permissions import SAFE_METHODS, BasePermission


class ProjectMessagePermission(BasePermission):
    """Anyone who can see the project can talk in it.

    Editing and deleting are limited to the author - a lead removing
    someone else's message from a conversation is not a feature anybody
    asked for.
    """

    def has_permission(self, request, view):
        return bool(request.user and request.user.is_authenticated)

    def has_object_permission(self, request, view, obj):
        if request.method in SAFE_METHODS:
            return True

        return obj.user == request.user or request.user.role == "ADMIN"
