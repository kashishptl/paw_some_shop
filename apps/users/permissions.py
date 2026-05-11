from rest_framework.permissions import BasePermission


def is_admin_or_manager(user):
    return (
        user
        and user.is_authenticated
        and user.role in ["admin", "manager"]
    )


class IsAdmin(BasePermission):
    def has_permission(self, request, view):
        return (
            request.user
            and request.user.is_authenticated
            and request.user.role == "admin"
        )


class IsManagerOrAdmin(BasePermission):
    def has_permission(self, request, view):
        return is_admin_or_manager(request.user)


class IsAdminOrManager(BasePermission):
    def has_permission(self, request, view):
        return is_admin_or_manager(request.user)