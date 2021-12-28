from django.db import models
from django.contrib.auth.models import AbstractUser


class User(AbstractUser):
    ADMIN = 'admin'
    MODERATOR = 'moderator'
    USER = 'user'

    ROLES_CHOICES = [
        (ADMIN, 'Администратор'),
        (MODERATOR, 'Модератор'),
        (USER, 'Пользователь'),
    ]

    STAFF = [
        ADMIN, MODERATOR
    ]

    role = models.CharField(
        max_length=30,
        choices=ROLES_CHOICES,
        default=USER,
    )
    # Если здесь нет какого-то поля, значит его реализация в базовом классе
    # Полностью совпадает с ТЗ
    first_name = models.CharField(max_length=150, blank=True)
    email = models.EmailField(max_length=254, unique=True)
    bio = models.CharField(max_length=256, blank=True)

    @property
    def is_admin(self):
        return self.role == self.ADMIN

    @property
    def is_personnel(self):
        return self.role in self.STAFF
