from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.db import models

import datetime as dt

User = get_user_model()

CHOICES = zip(range(1, 11), range(1, 11))


def validate_year(value):
    if value > dt.datetime.now().year:
        raise ValidationError(f'Указанный год больше нынешнего: {value}')


class Category(models.Model):
    name = models.CharField(max_length=256, verbose_name='Название')
    slug = models.SlugField(max_length=50, unique=True)

    class Meta:
        ordering = ['id']
        verbose_name = 'Категория'
        verbose_name_plural = 'Категории'

    def __str__(self):
        return self.name


class Genre(models.Model):
    name = models.CharField(max_length=256, verbose_name='Название')
    slug = models.SlugField(max_length=50, unique=True)

    class Meta:
        ordering = ['id']
        verbose_name = 'Жанр'
        verbose_name_plural = 'Жанры'

    def __str__(self):
        return self.name


class Title(models.Model):
    name = models.CharField(max_length=256, verbose_name='Название')
    year = models.PositiveSmallIntegerField(
        validators=(validate_year,), verbose_name='Год')
    description = models.TextField(verbose_name='Описание', blank=True)
    category = models.ForeignKey(
        Category, on_delete=models.PROTECT,
        related_name='categories', verbose_name='Категория')
    genre = models.ManyToManyField(
        Genre, related_name='genre', verbose_name='Жанр')

    class Meta:
        ordering = ['id']
        verbose_name = 'Произведение'
        verbose_name_plural = 'Произведения'

    def __str__(self):
        return self.name


class Review(models.Model):
    text = models.TextField(verbose_name='Текст')
    score = models.IntegerField(
        choices=CHOICES, default=1, verbose_name='Оценка')
    pub_date = models.DateTimeField(
        verbose_name='Дата публикации', auto_now_add=True)
    title = models.ForeignKey(
        Title, on_delete=models.CASCADE,
        related_name='reviews', verbose_name='Произведение')
    author = models.ForeignKey(
        User, on_delete=models.CASCADE,
        related_name='reviews', verbose_name='Автор')

    class Meta:
        ordering = ['-pub_date']
        verbose_name = 'Отзыв'
        verbose_name_plural = 'Отзывы'
        constraints = [
            models.UniqueConstraint(
                fields=['author', 'title'],
                name='unique_name_reviews'
            )
        ]

    def __str__(self):
        return self.text


class Comment(models.Model):
    pub_date = models.DateTimeField(
        verbose_name='Дата публикации', auto_now_add=True)
    author = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name='comments',
        verbose_name='Автор')
    review = models.ForeignKey(
        Review, on_delete=models.CASCADE,
        related_name='comments', verbose_name='Обзор')
    text = models.TextField(verbose_name='Текст')

    class Meta:
        ordering = ['-pub_date']
        verbose_name = 'Комментарий'
        verbose_name_plural = 'Комментарии'

    def __str__(self):
        return self.text
