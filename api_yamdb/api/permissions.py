from rest_framework import permissions


def is_staff(user):
    if user.role in ('admin', 'moderator'):
        return True
    
    return False


def is_admin(user):
    if user.role == 'admin':
        return True
    
    return False


class OnlyForAdmin(permissions.BasePermission):
    """
    Действия с этим пермишенном разрешены только с наличием роли админа.
    """

    def has_permission(self, request, view):
        return is_admin(request.user)


class ReadOnly(permissions.BasePermission):
    """
    Разрешено только чтение.
    """

    def has_permission(self, request, views):
        if request.method in permissions.SAFE_METHODS:
            return True

        return is_admin(request.user)


class IsAuthorOrReadOnly(permissions.BasePermission):
    """
    Разрешено изменение только своего контента.
    """

    def has_object_permission(self, request, views, obj):
        if request.method in permissions.SAFE_METHODS:
            return True

        return obj.author == request.user or is_staff(request.user)
