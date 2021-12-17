from rest_framework import permissions


class IsAuthorOrReadOnly(permissions.BasePermission):
    """
    Разрешено изменение только своего контента.
    """

    def has_object_permission(self, request, views, obj):
        if request.method in permissions.SAFE_METHODS:
            return True

        return obj.author == request.user


class IsYourProfileOrNothing(permissions.BasePermission):
    """
    Разрешено изменение только своего профиля.
    """

    def has_object_permission(self, request, views, obj):

        return obj.username == request.user.username
