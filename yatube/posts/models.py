from django.contrib.auth import get_user_model
from django.db import models

from .constants import SYMBOOL_LIMIT
from core.models import AbstractModel

User = get_user_model()


class Group(models.Model):
    title = models.CharField(max_length=200, verbose_name='Название')
    slug = models.SlugField(unique=True, verbose_name='Категория')
    description = models.TextField(verbose_name='Описание')

    def __str__(self):
        return self.title

    class Meta:
        verbose_name = 'Группа'
        verbose_name_plural = 'Группы'


class Post(AbstractModel):
    text = models.TextField(
        verbose_name='Текст поста',
        help_text='Введите текст поста',
    )

    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        verbose_name='Автор',
        related_name='posts',
    )

    group = models.ForeignKey(
        Group,
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
        verbose_name='Группа',
        related_name='posts',
        help_text='Группа, к которой будет относиться пост',
    )

    image = models.ImageField(
        'Картинка',
        upload_to='posts/',
        blank=True,
    )

    def __str__(self):
        return self.text[:SYMBOOL_LIMIT]

    class Meta:
        ordering = ('-pub_date',)
        verbose_name = 'Пост'
        verbose_name_plural = 'Посты'


class Comment(AbstractModel):
    post = models.ForeignKey(
        Post,
        verbose_name="Ссылка на пост",
        on_delete=models.CASCADE,
        related_name='comments',
    )
    author = models.ForeignKey(
        User,
        verbose_name='Ссылка на автора',
        on_delete=models.CASCADE,
        related_name='comments',
    )
    text = models.TextField(
        verbose_name='Текст комментария',
    )

    def __str__(self):
        return self.text

    class Meta:
        verbose_name = 'Коммент'
        verbose_name_plural = 'Комменты'


class Follow(models.Model):
    user = models.ForeignKey(
        User,
        verbose_name="Подписчик",
        on_delete=models.CASCADE,
        related_name='follower',  # разве лучше не follows?
    )
    author = models.ForeignKey(
        User,
        verbose_name="Автор",
        on_delete=models.CASCADE,
        related_name='following',  # followed
    )
    pub_date = models.DateTimeField(
        verbose_name='Дата подписки', auto_now_add=True
    )

    def __str__(self):
        return f'{self.user} подписался на {self.author}'

    class Meta:
        verbose_name = 'Подписка'
        verbose_name_plural = 'Подписки'
        constraints = [
            models.UniqueConstraint(
                fields=['user', 'author'], name='unique_subscription'
            )
        ]
