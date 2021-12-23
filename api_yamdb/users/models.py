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

    role = models.CharField(
        max_length=30,
        choices=ROLES_CHOICES,
        default=USER,
    )
    email = models.EmailField(unique=True)
    bio = models.CharField(max_length=256, blank=True)
    confirmation_code = models.IntegerField(blank=True, null=True)
