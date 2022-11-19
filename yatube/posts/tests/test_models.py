from django.test import TestCase

from ..constants import SYMBOOL_LIMIT
from ..models import Group, Post, User


class PostModelTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='auth')
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='Тестовый слаг',
            description='Тестовое описание',
        )
        cls.post = Post.objects.create(
            author=cls.user,
            text=('Тестовый пост для проверки 15 символов'),
        )

    def test_models_have_correct_object_names(self):
        """Проверяем, что у моделей корректно работает __str__."""
        group = PostModelTest.group
        str_group = group.__str__()
        self.assertEqual(str_group, 'Тестовая группа', 'Check group.__str__')

        post = PostModelTest.post
        str_post = post.__str__()[:SYMBOOL_LIMIT]
        self.assertEqual(str_post, 'Тестовый пост д', 'Check post.__str__')


    def test_post_verbose_name(self):
        """Проверяем, что verbose_name у модели Post совпадает с ожидаемым"""
        post = PostModelTest.post
        field_verboses = {
            'text': 'Текст поста',
            'pub_date': 'Дата публикации',
            'author': 'Автор',
            'group': 'Группа',
            'image': 'Картинка'
        }
    
        for field, expected_value in field_verboses.items():
            with self.subTest(field=field):
                self.assertEqual(
                    post._meta.get_field(field).verbose_name,
                    expected_value,
                )


    def test_post_help_text(self):
        """Проверяем, что help_text у модели Post совпадает с ожидаемым"""
        post = PostModelTest.post
        field_help_text = {
            'text': 'Введите текст поста',
            'group': 'Группа, к которой будет относиться пост',
        }
        for field, expected_value in field_help_text.items():
            with self.subTest(field=field):
                self.assertEqual(
                    post._meta.get_field(field).help_text,
                    expected_value,
                )
