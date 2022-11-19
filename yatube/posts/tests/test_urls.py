from http import HTTPStatus

from django.test import TestCase, Client
from django.urls import reverse

from posts.models import Group, Post, User


class PostURLTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='author')
        cls.user2 = User.objects.create_user(username='justuser')
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='test-slug',
            description='Тестовое описание',
        )
        cls.post = Post.objects.create(
            text='Тестовый текст',
            author=cls.user,
        )

    def setUp(self):
        self.guest_client = Client()
        self.user = PostURLTests.user
        self.user2 = PostURLTests.user2
        self.authorized_client = Client()
        self.authorized_client2 = Client()
        self.authorized_client.force_login(self.user)
        self.authorized_client2.force_login(self.user2)

    def test_unauthorized_user_opens_pages(self):
        """
        Неавторизованный пользователь открывает страницы:
        ('index', 'group_list', 'profile', 'post_detail',
        и пробует открыть несуществующую /unexisiting_page/)
        """
        pages = {
            reverse('posts:index'): HTTPStatus.OK,
            reverse(
                'posts:group_list', kwargs={'slug': 'test-slug'}
            ): HTTPStatus.OK,
            reverse(
                'posts:profile', kwargs={'username': 'author'}
            ): HTTPStatus.OK,
            reverse('posts:post_detail', kwargs={'post_id': 1}): HTTPStatus.OK,
            '/unexisiting_page/': HTTPStatus.NOT_FOUND,
        }

        for url, status in pages.items():
            with self.subTest(status=status):
                response = self.guest_client.get(url)
                self.assertEqual(response.status_code, status)

    def test_post_edit_opens_only_for_author(self):
        """
        Страница редактирования поста доступна только АВТОРУ поста
        и делает редирект на страницу поста для НЕ автора
        """
        response = self.authorized_client.get(
            reverse('posts:post_edit', kwargs={'post_id': '1'})
        )
        self.assertEqual(response.status_code, HTTPStatus.OK)

        response = self.authorized_client2.get(
            reverse('posts:post_edit', kwargs={'post_id': '1'}), follow=True
        )
        self.assertRedirects(
            response, reverse('posts:post_detail', kwargs={'post_id': '1'})
        )

    def test_post_create_opens_only_for_autorised(self):
        """
        Страница создания поста доступна только авторизованному пользователю
        и делает редирект на страницу логина для стороннего
        """
        response = self.authorized_client.get(reverse('posts:post_create'))
        self.assertEqual(response.status_code, HTTPStatus.OK)

        response = self.guest_client.get(
            reverse('posts:post_create'), follow=True
        )
        self.assertRedirects(
            response,
            f'{reverse("users:login")}?next={reverse("posts:post_create")}',
        )
