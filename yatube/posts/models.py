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


class Follow(AbstractModel):
    user = models.ForeignKey(
        User,
        verbose_name="Подписчик",
        on_delete=models.CASCADE,
        related_name='follower',  # разве лучше follows?
    )
    author = models.ForeignKey(
        User,
        verbose_name="Автор",
        on_delete=models.CASCADE,
        related_name='following',  #  followed
    )

    def __str__(self):
        return f'{self.user} подписан на {self.author}'
